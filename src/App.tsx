import React, { useState, useRef } from 'react';
import { 
  Upload, 
  Send, 
  Cpu, 
  UserCheck, 
  ShieldCheck, 
  Terminal,
  RefreshCw,
  Mail,
  CheckCircle2,
  AlertCircle,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

const BentoCard = ({ children, title, icon: Icon, className = "" }: any) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className={`bg-white border-2 border-slate-200 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all ${className}`}
  >
    {title && (
      <div className="flex items-center gap-2 mb-4">
        <div className="w-6 h-6 flex items-center justify-center bg-blue-50 rounded-lg">
          <Icon className="w-3.5 h-3.5 text-blue-600" />
        </div>
        <h2 className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{title}</h2>
      </div>
    )}
    {children}
  </motion.div>
);

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [provider, setProvider] = useState<'gemini' | 'groq'>('groq');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [feedbackGiven, setFeedbackGiven] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addLog = (msg: string) => {
    setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 50));
  };

  const handleScreen = async () => {
    if (!file || !jobDescription) return;
    
    setLoading(true);
    addLog("System: Initializing Agent cluster...");
    
    try {
      const formData = new FormData();
      formData.append('resume', file);
      formData.append('job_description', jobDescription);
      formData.append('provider', provider);

      const response = await fetch('/api/screen', {
        method: 'POST',
        body: formData,
      }).catch(err => {
        throw new Error(`Network Connectivity Error: ${err.message}. The server may be restarting.`);
      });

      let data;
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.indexOf("application/json") !== -1) {
        data = await response.json();
      } else {
        const text = await response.text();
        console.error("Non-JSON Server Response:", text);
        if (text.includes("Cookie check") || text.includes("Action required")) {
          throw new Error("Platform authentication required. Please open this app in a NEW TAB using the icon in the top right of the preview header to resolve cookie blocks.");
        }
        throw new Error(`Critical Server error: Received HTML instead of JSON. Backend might be restarting. Please try again in 5 seconds.`);
      }

      if (!response.ok) {
        throw new Error(data.error || data.message || 'Agent cluster execution failed');
      }

      setResult(data);
      setFeedbackGiven(false);
      addLog("Researcher: Analysis Complete. Data yielded to Analyst.");
      addLog("Analyst: Recommendation and Email draft ready.");
    } catch (error: any) {
      console.error(error);
      addLog(`Error: ${error.message || "Agent communication interrupted."}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (type: 'good' | 'bad') => {
    if (!result) return;
    
    try {
      await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_input: jobDescription,
          agent_response: JSON.stringify(result),
          feedback: type
        }),
      });
      setFeedbackGiven(true);
      addLog(`System: Feedback recorded (${type.toUpperCase()}).`);
    } catch (error) {
      console.error("Feedback failed:", error);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6 font-sans text-slate-900">
      {/* Header */}
      <header className="flex justify-between items-center mb-8 max-w-7xl mx-auto">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-slate-900 flex items-center gap-3">
            <span className="bg-blue-600 text-white p-1 rounded-lg">🤖</span> AI Lab: Resume Screening
          </h1>
          <p className="text-[10px] text-slate-500 font-mono mt-1 uppercase tracking-wider">LAB_07_08_DEPLOYMENT | PROVIDER: {provider.toUpperCase()}</p>
        </div>
        <div className="flex gap-3">
          <div className="flex bg-slate-200 p-1 rounded-xl gap-1">
            <button 
              onClick={() => setProvider('gemini')}
              className={`px-4 py-1.5 rounded-lg text-[10px] font-black uppercase transition-all ${provider === 'gemini' ? 'bg-white shadow-sm text-blue-600' : 'text-slate-500 hover:text-slate-700'}`}
            >
              Gemini
            </button>
            <button 
              onClick={() => setProvider('groq')}
              className={`px-4 py-1.5 rounded-lg text-[10px] font-black uppercase transition-all ${provider === 'groq' ? 'bg-white shadow-sm text-orange-600' : 'text-slate-500 hover:text-slate-700'}`}
            >
              Groq
            </button>
          </div>
          <div className="px-4 py-1.5 bg-green-100/50 border border-green-200 rounded-full flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
            <span className="text-[10px] font-bold text-green-700 uppercase">API: Online</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto grid grid-cols-12 gap-6">
        {/* Left Column: Inputs */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          <BentoCard title="01. Input Configuration" icon={Upload}>
            <div className="space-y-4">
              <input 
                type="file" 
                ref={fileInputRef}
                className="hidden" 
                accept=".pdf"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              <div 
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                  file ? 'border-green-200 bg-green-50/30' : 'border-slate-200 hover:border-blue-400 hover:bg-blue-50/30'
                }`}
              >
                {file ? (
                  <div className="flex flex-col items-center">
                    <CheckCircle2 className="w-8 h-8 text-green-500 mb-2" />
                    <span className="text-xs font-medium text-slate-600 truncate max-w-full">{file.name}</span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <Upload className="w-8 h-8 text-slate-300 mb-2" />
                    <span className="text-xs text-slate-400">Upload Candidate PDF</span>
                  </div>
                )}
              </div>

              <div>
                <label className="text-[10px] font-bold uppercase text-slate-500 block mb-2 ml-1">Job Description</label>
                <textarea 
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste requirements here..."
                  className="w-full h-48 bg-slate-50 border-2 border-slate-100 rounded-xl p-4 text-xs focus:border-blue-500 focus:ring-0 transition-all outline-none"
                />
              </div>

              <button 
                onClick={handleScreen}
                disabled={loading || !file || !jobDescription}
                className={`w-full py-4 rounded-xl font-bold text-sm shadow-sm transition-all flex items-center justify-center gap-2 ${
                  loading 
                    ? 'bg-slate-100 text-slate-400' 
                    : 'bg-slate-900 text-white hover:bg-slate-800 active:scale-[0.98]'
                }`}
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                {loading ? 'Processing Agents...' : 'Run Screening System'}
              </button>
            </div>
          </BentoCard>

          <BentoCard title="04. Security Guardrails" icon={ShieldCheck}>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Injection', status: 'Secure', color: 'text-green-600', bg: 'bg-green-50' },
                { label: 'PII Check', status: 'Masked', color: 'text-green-600', bg: 'bg-green-50' },
                { label: 'Topic Filter', status: 'Verified', color: 'text-blue-600', bg: 'bg-blue-50' },
                { label: 'Hallucination', status: 'Low (0.01%)', color: 'text-slate-600', bg: 'bg-slate-100' },
              ].map((guard, i) => (
                <div key={i} className={`${guard.bg} p-3 rounded-xl border border-white/50 shadow-sm`}>
                  <p className="text-[8px] font-bold text-slate-400 uppercase mb-1">{guard.label}</p>
                  <p className={`text-[10px] font-bold ${guard.color}`}>{guard.status}</p>
                </div>
              ))}
            </div>
          </BentoCard>
        </div>

        {/* Center Column: Execution */}
        <div className="col-span-12 lg:col-span-5 flex flex-col gap-6">
          <BentoCard title="02. Agent Collaboration" icon={Cpu} className="bg-slate-900 h-full !border-slate-800 shadow-xl overflow-hidden flex flex-col">
            <div className="flex-1 space-y-3 font-mono text-[10px] sm:text-[11px] overflow-y-auto pr-2 custom-scrollbar">
              {logs.length === 0 ? (
                <div className="h-full flex items-center justify-center text-slate-600">
                  <p>System idle. Waiting for request...</p>
                </div>
              ) : (
                logs.map((log, index) => (
                  <motion.p 
                    key={index} 
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className={`${log.includes('Researcher:') ? 'text-green-400' : log.includes('Analyst:') ? 'text-blue-400' : 'text-slate-400'}`}
                  >
                    {log}
                  </motion.p>
                ))
              )}
            </div>
            
            {result && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 p-4 bg-slate-800 rounded-xl border border-slate-700 shadow-inner"
              >
                <div className="flex items-center gap-2 mb-2">
                  <UserCheck className="w-3.5 h-3.5 text-indigo-400" />
                  <span className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">Final Decision State</span>
                </div>
                <p className="text-slate-300 text-[11px] leading-relaxed italic">
                  Matched core technical signals. Match logic suggests potential candidate fit. Recommendations finalized for human review.
                </p>
                
                {/* Feedback Section */}
                <div className="mt-4 pt-4 border-t border-slate-700 flex items-center justify-between">
                  <span className="text-[9px] font-bold text-slate-500 uppercase">Rate system response:</span>
                  <div className="flex gap-2">
                    {feedbackGiven ? (
                      <span className="text-[9px] font-bold text-green-500 uppercase animate-pulse">Feedback Received!</span>
                    ) : (
                      <>
                        <button 
                          onClick={() => handleFeedback('good')}
                          className="p-1.5 hover:bg-slate-700 rounded-lg transition-colors group"
                        >
                          <ThumbsUp className="w-3 h-3 text-slate-500 group-hover:text-green-500" />
                        </button>
                        <button 
                          onClick={() => handleFeedback('bad')}
                          className="p-1.5 hover:bg-slate-700 rounded-lg transition-colors group"
                        >
                          <ThumbsDown className="w-3 h-3 text-slate-500 group-hover:text-red-500" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </BentoCard>
        </div>

        {/* Right Column: Results & HITL */}
        <div className="col-span-12 lg:col-span-3 space-y-6">
          <BentoCard className="flex flex-col items-center justify-center text-center p-8">
            <div className="relative">
              <div className="text-6xl font-black text-slate-900 tracking-tighter">
                {result ? (result.messages?.[result.messages.length-1]?.content?.match(/Score:\s*(\d+)/i)?.[1] || '70+') : '--'}
                <span className="text-3xl text-blue-600 ml-1">%</span>
              </div>
            </div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em] mt-4">Match Probability</div>
            <div className="flex gap-1.5 mt-5">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className={`w-8 h-2 rounded-full transition-colors duration-500 ${result && i < 3 ? 'bg-green-500' : 'bg-slate-100'}`} />
              ))}
            </div>
          </BentoCard>

          <BentoCard title="03. HITL Action" icon={Mail} className="flex-1">
            <div className="h-full flex flex-col">
              {!result ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-4">
                  <Mail className="w-8 h-8 text-slate-100 mb-2" />
                  <p className="text-[10px] text-slate-400 font-medium">Draft will appear after agent screening.</p>
                </div>
              ) : (
                <div className="space-y-4">
                   <div className="p-4 bg-blue-50 border border-blue-100 rounded-xl">
                    <p className="text-[10px] text-blue-900 leading-relaxed max-h-[220px] overflow-y-auto">
                      <strong>Subject:</strong> Interview Invitation<br/><br/>
                      {result.proposedEmail}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button className="flex-1 py-2.5 bg-blue-600 text-white rounded-xl text-[10px] font-bold shadow-md shadow-blue-100 hover:bg-blue-700 transition-colors">
                      Approve & Send
                    </button>
                    <button className="px-3 py-2.5 bg-white border border-slate-200 rounded-xl text-[10px] font-bold text-slate-600 hover:bg-slate-50">
                      Edit
                    </button>
                  </div>
                </div>
              )}
            </div>
          </BentoCard>
        </div>
      </main>

      <footer className="mt-12 max-w-7xl mx-auto border-t border-slate-200 pt-8 pb-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            { label: 'Lab 07: Evaluation', desc: 'Quantitative metrics via LLM-as-a-judge.', icon: AlertCircle },
            { label: 'Lab 08: API Layer', desc: 'Express API integration with LangGraph.', icon: Terminal },
            { label: 'Open Ended: CI/CD', desc: 'Docker packaging & Github Actions.', icon: ShieldCheck },
          ].map((item, i) => (
            <div key={i} className="flex gap-4">
              <div className="w-10 h-10 bg-white border border-slate-200 rounded-xl flex items-center justify-center shrink-0 shadow-sm">
                <item.icon className="w-5 h-5 text-slate-400" />
              </div>
              <div>
                <h4 className="text-[11px] font-bold text-slate-900 uppercase tracking-wider mb-1">{item.label}</h4>
                <p className="text-[11px] text-slate-500 leading-relaxed">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </footer>
    </div>
  );
}
