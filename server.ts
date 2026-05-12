import 'dotenv/config';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const pdf = require('pdf-parse');

import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";
import multer from "multer";
import fs from "fs/promises";
import { existsSync } from "fs";
import { app as graphApp } from "./src/lib/agents";
import { HumanMessage } from "@langchain/core/messages";

async function startServer() {
  const app = express();
  const PORT = 3000;
  const upload = multer();

  app.use(express.json());

  // Logging middleware
  app.use((req, res, next) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
    next();
  });

  // Check for API Keys early
  if (!process.env.GROQ_API_KEY && !process.env.GEMINI_API_KEY) {
    console.warn("WARNING: No AI API keys (GROQ_API_KEY or GEMINI_API_KEY) are set. The agent features will fail.");
  }

  // API Routes
  app.post("/api/screen", upload.single('resume'), async (req: any, res) => {
    console.log("API: /api/screen called");
    try {
      const { job_description, provider = "groq" } = req.body;
      const file = req.file;

      if (!file || !job_description) {
        console.error("API Error: Missing file or job description");
        return res.status(400).json({ error: "Missing file or job description" });
      }

      // 1. Parse PDF
      console.log("System: Parsing PDF resume...");
      let resumeText = "";
      try {
        const data = await pdf(file.buffer);
        resumeText = data.text;
        console.log(`System: Successfully extracted ${resumeText?.length || 0} characters.`);
        if (!resumeText) throw new Error("Extracted text is empty");
      } catch (pdfErr) {
        console.error("PDF Parse Error:", pdfErr);
        throw new Error("Failed to parse PDF resume or PDF is empty/corrupt.");
      }

      // 2. Initialize Agent Graph
      const threadId = `session-${Date.now()}`;
      console.log(`Agent: Initializing graph for thread ${threadId}`);
      
      const initialState = {
        messages: [
          new HumanMessage(`RECRUITMENT REQUEST:
          Candidate Resume:
          ${resumeText}
          
          Job Requirements:
          ${job_description}`)
        ],
        researchDone: false,
        proposedEmail: null,
        approved: false,
        researchSteps: 0
      };

      const result = await graphApp.invoke(initialState, {
        configurable: { 
          thread_id: threadId,
          provider: provider
        }
      });

      console.log("Agent: Execution successful");
      res.json({
        threadId,
        messages: result.messages,
        proposedEmail: result.proposedEmail,
        researchSteps: result.researchSteps,
        researchDone: result.researchDone
      });

    } catch (error: any) {
      console.error("Server Error:", error);
      res.status(500).json({ error: error.message || "Agent execution failed" });
    }
  });

  app.post("/api/feedback", async (req, res) => {
    try {
      const { user_input, agent_response, feedback } = req.body;
      const logEntry = {
        timestamp: new Date().toISOString(),
        user_input,
        agent_response,
        feedback
      };

      const logPath = path.join(process.cwd(), 'feedback_log.json');
      let logs = [];
      
      if (existsSync(logPath)) {
        const fileContent = await fs.readFile(logPath, 'utf8');
        try {
          logs = JSON.parse(fileContent);
        } catch (e) {
          logs = [];
        }
      }
      
      logs.push(logEntry);
      await fs.writeFile(logPath, JSON.stringify(logs, null, 2));
      
      console.log(`System: Feedback recorded for "${user_input.slice(0, 30)}..."`);
      res.json({ success: true });
    } catch (error: any) {
      console.error("Feedback Error:", error);
      res.status(500).json({ error: "Failed to save feedback" });
    }
  });

  // Global Error Handler
  app.use((err: any, req: any, res: any, next: any) => {
    console.error("Global Error Handler Catch:", err);
    if (!res.headersSent) {
      res.status(500).json({ 
        error: "Internal Server Error", 
        message: err.message,
        stack: process.env.NODE_ENV === "production" ? undefined : err.stack
      });
    }
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer().catch(err => {
  console.error("Failed to start server:", err);
  process.exit(1);
});
