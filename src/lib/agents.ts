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
    const apiKey = process.env.GROQ_API_KEY || process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
    if (!apiKey) {
      return JSON.stringify({ error: "Missing API Key for semantic scoring." });
    }

    try {
      // Use a fast model for semantic evaluation
      const model = process.env.GROQ_API_KEY 
        ? new ChatGroq({ model: "llama-3.3-70b-versatile", apiKey: process.env.GROQ_API_KEY, temperature: 0 })
        : new ChatGoogleGenerativeAI({ model: "gemini-1.5-flash", apiKey: apiKey, temperature: 0 });

      const prompt = `Evaluate the following Resume against the Job Description. 
      Provide a match score (0-100) based on semantic fit, experience level, and skill relevance.
      Do NOT just match keywords; look for transferable skills and relevant experience.
      
      Resume:
      ${resume_text.slice(0, 4000)}
      
      Job Description:
      ${job_description.slice(0, 2000)}
      
      Return ONLY a JSON object with the following keys:
      - score: number (0-100)
      - reasons: string[] (top 3 reasons for the score)
      - strengths: string[]
      - gaps: string[]
      - verdict: string (S-Tier, Qualified, Borderline, or Reject)`;

      const response = await model.invoke([new HumanMessage(prompt)]);
      const content = response.content as string;
      
      // Attempt to extract JSON if the model added markdown blocks
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      const result = jsonMatch ? JSON.parse(jsonMatch[0]) : JSON.parse(content);
      
      return JSON.stringify(result);
    } catch (err: any) {
      return JSON.stringify({ 
        error: "Semantic evaluation failed", 
        details: err.message,
        score: 50, // Default fallback
        reasons: ["Evaluation service temporary error"]
      });
    }
  },
  {
    name: "calculate_match_score",
    description: "Performs a semantic evaluation of a resume against a job description using an LLM.",
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
  3. The tool will provide a SEMANTIC score and detailed REASONS. 
  4. Summarize these findings for the Analyst, specifically highlighting the reasons provided by the tool.`);

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
  Review the research (score, reasons, strengths, gaps) and write a professional email to the candidate.
  - S-Tier/Qualified: Interview invite, mention their specific strengths.
  - Borderline/Reject: Polite rejection, mentioning some of the gaps or missing alignment based on the research.
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
