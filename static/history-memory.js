(() => {
  "use strict";
  const $ = (selector) => document.querySelector(selector);
  let entries = [];
  let loaded = false;
  const labels = { lesson:"Lesson", practice:"Project practice", interview:"Career studio", review:"Memory review" };
  const symbols = { lesson:"L", practice:"P", interview:"C", review:"M" };
  function el(tag, cls, text) { const n=document.createElement(tag); if(cls)n.className=cls; if(text!==undefined)n.textContent=String(text); return n; }
  async function loadTimeline() {
    const list=$("#history-timeline-list"), note=$("#history-timeline-note");
    if(!list||!note)return;
    list.replaceChildren(); note.textContent="Loading saved activity…";
    try {
      const response=await fetch("/api/progress/overview",{cache:"no-store"});
      const data=await response.json();
      if(!response.ok)throw new Error(data.detail||"Could not load history.");
      entries=Array.isArray(data.recent_activity)?data.recent_activity:[];
      loaded=true; render();
    } catch(error) { note.textContent=error.message; note.classList.add("error"); }
  }
  function render() {
    const list=$("#history-timeline-list"), note=$("#history-timeline-note");
    if(!list||!note)return;
    list.replaceChildren();
    const query=$("#history-search").value.trim().toLocaleLowerCase();
    const filter=$("#history-filter").value;
    const filtered=entries.filter(item=>(filter==="all"||item.type===filter)&&(!query||String(item.title+" "+(labels[item.type]||item.type)).toLocaleLowerCase().includes(query)));
    note.classList.remove("error");
    note.textContent=filtered.length+" of "+entries.length+" saved activities · records of practice, not a score.";
    if(!filtered.length){list.append(el("p","history-empty",entries.length?"No activity matches this search and filter.":"Your completed lessons, practice, interviews, and memory reviews will appear here as you use Prepped."));return;}
    for(const item of filtered) {
      const row=el("article","history-timeline-entry");
      row.append(el("span","history-timeline-symbol",symbols[item.type]||"•"));
      const copy=el("div");
      copy.append(el("h4","",item.title),el("p","",(labels[item.type]||"Activity")+" · "+(item.occurred_at?new Date(item.occurred_at).toLocaleString():"Date unavailable")));
      row.append(copy);
      const action=el("button","button button-quiet",item.type==="practice"?"Open session":item.type==="interview"?"Open Career":item.type==="review"?"Open Memory":"Open Learn");
      action.type="button";
      action.addEventListener("click",()=>open(item));
      row.append(action); list.append(row);
    }
  }
  async function open(item) {
    if(item.type==="practice") {
      $("#history-toggle").click();
      const button=await wait("#history-list [data-session-id]",item.id);
      button?.click(); return;
    }
    if(item.type==="interview") {
      $("#career-toggle").click();
      const button=await wait("#career-history-list [data-session-id]",item.id);
      button?.click(); return;
    }
    $("#learning-toggle").click();
    if(item.type==="review") $("#memory-view")?.scrollIntoView({behavior:"smooth",block:"start"});
    else $("#learning-resume-list")?.scrollIntoView({behavior:"smooth",block:"start"});
  }
  async function wait(selector,id) {
    for(let i=0;i<180;i++){const b=[...document.querySelectorAll(selector)].find(x=>x.dataset.sessionId===id);if(b)return b;await new Promise(r=>requestAnimationFrame(r));}
    return null;
  }
  document.addEventListener("DOMContentLoaded",()=>{
    $("#history-toggle")?.addEventListener("click",()=>{if(!loaded)loadTimeline();});
    $("#history-timeline-refresh")?.addEventListener("click",loadTimeline);
    $("#history-search")?.addEventListener("input",render);
    $("#history-filter")?.addEventListener("change",render);
  });
})();