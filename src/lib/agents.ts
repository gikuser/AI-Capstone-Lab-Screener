import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { ChatGroq } from "@langchain/groq";
import { 
  StateGraph, 
  START, 
  END, 
  MemorySaver,
  Annotation
} from "@langchain/langgraph";
import { 
  BaseMessage, 
  HumanMessage, 
  AIMessage, 
  SystemMessage,
  ToolMessage
} from "@langchain/core/messages";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

// --- State Definition ---
export const AgentAnnotation = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (x, y) => x.concat(y),
  }),
  researchDone: Annotation<boolean>,
  proposedEmail: Annotation<string | null>,
  approved: Annotation<boolean>,
  researchSteps: Annotation<number>,
});

// --- Tools ---

export const calculateMatchScore = tool(
  async ({ resume_text, job_description }) => {
    const resumeKw = resume_text.toLowerCase().split(/\W+/);
    const jobKw = job_description.toLowerCase().split(/\W+/).filter(w => w.length > 3);
    
    const matched = jobKw.filter(w => resumeKw.includes(w));
    const missing = jobKw.filter(w => !resumeKw.includes(w));
    
    const score = jobKw.length > 0 ? Math.round((matched.length / jobKw.length) * 100) : 0;
    
    return JSON.stringify({
      score,
      matched_skills: matched.slice(0, 10),
      missing_skills: missing.slice(0, 10),
      verdict: score >= 70 ? "Strong Match" : score >= 40 ? "Partial Match" : "Weak Match"
    });
  },
  {
    name: "calculate_match_score",
    description: "Analyzes a resume against a job description to calculate a match score.",
    schema: z.object({
      resume_text: z.string(),
      job_description: z.string(),
    }),
  }
);

// --- Models ---
const getModel = (config: any, withTools = false) => {
  const provider = config?.configurable?.provider || "groq";
  
  if (provider === "groq") {
    const apiKey = process.env.GROQ_API_KEY;
    if (!apiKey) {
      throw new Error("Missing GROQ_API_KEY. Please set it in the platform settings.");
    }
    const model = new ChatGroq({
      model: "llama-3.3-70b-versatile",
      apiKey: apiKey,
      temperature: 0,
    });
    return withTools ? model.bindTools([calculateMatchScore]) : model;
  } else {
    const apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
    if (!apiKey || apiKey.includes("MY_GEMINI_API_KEY")) {
      throw new Error("Gemini API key is missing. Please ensure GEMINI_API_KEY is configured in the Secrets/Settings panel.");
    }

    const model = new ChatGoogleGenerativeAI({
      model: "gemini-1.5-flash",
      apiKey: apiKey,
      temperature: 0,
    });

    return withTools ? model.bindTools([calculateMatchScore]) : model;
  }
};

// --- Nodes ---

const researchAgent = async (state: typeof AgentAnnotation.State, config?: any) => {
  console.log(`Agent: Research Agent acting with [${config?.configurable?.provider || 'default'}]...`);
  const steps = state.researchSteps || 0;
  
  if (steps >= 3) {
    console.log("Agent: Research limit reached.");
    return { 
      messages: [new AIMessage("RESEARCH_LIMIT_REACHED: Proceeding with available data.")],
      researchDone: true 
    };
  }

  const systemMsg = new SystemMessage(`You are a technical Researcher. 
  1. ALWAYS call calculate_match_score with the PROVIDED Candidate Resume and Job Requirements.
  2. You MUST use the exact text from the state messages.
  3. Once you have the tech score, summarize the findings and set researchDone to true by stopping tool calls.`);

  const modelWithTools = getModel(config, true);
  const response = await modelWithTools.invoke([systemMsg, ...state.messages]);
  
  const isDone = response.tool_calls && response.tool_calls.length === 0 && steps > 0;
  console.log(`Agent: Researcher state - steps: ${steps + 1}, isDone: ${isDone}`);

  return { 
    messages: [response], 
    researchSteps: steps + 1,
    researchDone: isDone
  };
};

const analysisAgent = async (state: typeof AgentAnnotation.State, config?: any) => {
  console.log(`Agent: Analysis Agent acting with [${config?.configurable?.provider || 'default'}]...`);
  const systemMsg = new SystemMessage(`You are a senior Hiring Analyst. 
  Review the research and write a professional email to the candidate.
  - Score >= 40: Interview invite.
  - Score < 40: Rejection.
  Sign off as 'AI Hiring Team'.`);

  const model = getModel(config, false);
  const response = await model.invoke([systemMsg, ...state.messages]);
  console.log("Agent: Email draft generated.");
  return { 
    messages: [response], 
    proposedEmail: response.content as string,
    approved: false 
  };
};

const toolNode = async (state: typeof AgentAnnotation.State) => {
  const lastMsg = state.messages[state.messages.length - 1] as AIMessage;
  const results: ToolMessage[] = [];
  
  if (lastMsg.tool_calls) {
    for (const call of lastMsg.tool_calls) {
      console.log(`Agent: Executing tool ${call.name}...`);
      if (call.name === "calculate_match_score") {
        try {
          const obs = await calculateMatchScore.invoke(call.args as any);
          results.push(new ToolMessage({
            content: typeof obs === 'string' ? obs : JSON.stringify(obs),
            tool_call_id: call.id!,
          }));
        } catch (err: any) {
          console.error(`Agent: Tool Error: ${err.message}`);
          results.push(new ToolMessage({
            content: `Error executing tool: ${err.message}`,
            tool_call_id: call.id!,
          }));
        }
      }
    }
  }
  return { messages: results };
};

// --- Router ---
const router = (state: typeof AgentAnnotation.State) => {
  const lastMsg = state.messages[state.messages.length - 1];
  if (lastMsg instanceof AIMessage && lastMsg.tool_calls && lastMsg.tool_calls.length > 0) {
    return "tools";
  }
  if (state.researchDone) return "analysis";
  return "research";
};

// --- Graph ---
const workflow = new StateGraph(AgentAnnotation)
  .addNode("research", researchAgent)
  .addNode("tools", toolNode)
  .addNode("analysis", analysisAgent)
  .addEdge(START, "research")
  .addConditionalEdges("research", router, {
    tools: "tools",
    analysis: "analysis",
    research: "research"
  })
  .addEdge("tools", "research")
  .addEdge("analysis", END);

export const app = workflow.compile({
  checkpointer: new MemorySaver()
});
