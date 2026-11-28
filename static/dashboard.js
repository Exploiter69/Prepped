(() => {
"use strict";
const $=selector=>document.querySelector(selector);
let loading=false;
async function request(url){const response=await fetch(url,{headers:{Accept:"application/json"}});const body=await response.json().catch(()=>({}));if(!response.ok)throw new Error(typeof body.detail==="string"?body.detail:"This dashboard section could not be loaded.");return body;}
function node(tag,className,text){const element=document.createElement(tag);if(className)element.className=className;if(text!==undefined&&text!==null)element.textContent=String(text);return element;}
function localDate(){const now=new Date(),offset=now.getTimezoneOffset();return new Date(now.getTime()-offset*60000).toISOString().slice(0,10);}
function renderPath(catalog,progress){
 const target=$("#dashboard-path-preview");target.replaceChildren();const recommendation=catalog.recommendations||{};
 const track=(catalog.tracks||[]).find(item=>item.id===recommendation.track_id)||catalog.tracks?.[0];
 if(!track){target.append(node("p","dashboard-muted","Your learning path is not available yet. Open Learn to explore the curriculum."));return;}
 $("#dashboard-track-description").textContent=track.title+" · "+(track.description||recommendation.track_description||"A path built around your learning goals.");
 const completed=new Set(progress.completed_lesson_ids||[]),lessons=track.lessons||[],next=lessons.filter(item=>!completed.has(item.id)).slice(0,3),visible=next.length?next:lessons.slice(0,3);
 visible.forEach((lesson,index)=>{const done=completed.has(lesson.id),row=node("article","dashboard-lesson"+(done?" is-complete":"")),marker=node("span","dashboard-lesson-marker",done?"✓":String(index+1)),copy=node("div");marker.setAttribute("aria-hidden","true");copy.append(node("h3","",lesson.title),node("p","",lesson.summary||"A short guided practice session."));row.append(marker,copy,node("span","dashboard-lesson-status",done?"COMPLETED":(lesson.estimated_minutes||8)+" MIN"));if(index===0&&!done){const action=node("button","button button-secondary dashboard-lesson-action","Start lesson");action.type="button";action.setAttribute("aria-label","Start lesson: "+lesson.title);action.addEventListener("click",()=>window.dispatchEvent(new CustomEvent("prepped:start-lesson",{detail:{lessonId:lesson.id}})));row.append(action);}target.append(row);});
 if(!visible.length)target.append(node("p","dashboard-muted","No lessons are available in this path yet."));
 if(!next.length&&lessons.length)target.append(node("p","dashboard-complete-note","You have completed the lessons currently listed in this path. You can revisit them in Learn."));
}
function renderPlan(result){
 const target=$("#dashboard-plan-preview");target.replaceChildren();const items=result.plan?.items||[];
 if(!items.length){target.append(node("p","dashboard-muted","No plan yet for today. Build a 10–30 minute checklist in one click."));const cta=node("button","button button-secondary dashboard-empty-plan-btn","Build today’s plan →");cta.type="button";cta.addEventListener("click",()=>{window.PreppedApp?.showView("progress-view");window.PreppedUI?.setProgressTab?.("plan");});target.append(cta);return;}
 items.slice(0,4).forEach((item,index)=>{const row=node("div","dashboard-plan-item"),copy=node("div");row.append(node("span","",item.status==="completed"?"✓":String(index+1)));copy.append(node("strong","",item.title),node("small","",(item.estimated_minutes||0)+" min · "+String(item.status||"planned").replaceAll("_"," ")));row.append(copy);target.append(row);});
 if(items.length>4)target.append(node("p","dashboard-muted",(items.length-4)+" more activities in your plan."));
}
function renderStats(progress,overview){$("#dashboard-lessons-completed").textContent=String(progress.lessons_completed??0);$("#dashboard-skills-active").textContent=String(overview.summary?.skills_with_activity??0);$("#dashboard-reviews-due").textContent=String(overview.summary?.due_memory_items??0);}
async function loadDashboard(){
 if(loading)return;loading=true;
 try{
  const results=await Promise.allSettled([request("/api/profile"),request("/api/learning/catalog"),request("/api/learning/progress"),request("/api/intelligence/overview"),request("/api/intelligence/plan?plan_date="+encodeURIComponent(localDate())),request("/api/memory/review/queue")]);
  const [profileResult,catalogResult,progressResult,overviewResult,planResult,memoryQueueResult]=results;
  const failedSections=results.slice(0,5).flatMap((result,index)=>result.status==="rejected"?[["profile","learning path","lesson activity","learning summary","today’s plan"][index]]:[]);
  const status=$("#dashboard-load-status");if(status)status.textContent=failedSections.length?"Some dashboard details could not be refreshed: "+failedSections.join(", ")+". Refresh to try again.":"Dashboard refreshed. Your saved activity is up to date.";
  if(profileResult.status==="fulfilled"){const profile=profileResult.value.profile,name=profile?.display_name?.trim();$("#dashboard-greeting").textContent=name?"WELCOME BACK, "+name.toUpperCase():"TODAY";const labels={english_fluency:"Build confidence and fluency in everyday English.",placement_interviews:"Prepare to communicate clearly in placement conversations.",technical_interviews:"Practise explaining technical ideas with clarity.",project_communication:"Get better at explaining the work you do.",professional_communication:"Build clear, confident professional communication."};if(profile?.primary_goal)$("#dashboard-goal").textContent=labels[profile.primary_goal]||"Build clear English and interview confidence, one short session at a time.";}
  if(catalogResult.status==="fulfilled"&&progressResult.status==="fulfilled")renderPath(catalogResult.value,progressResult.value);else $("#dashboard-track-description").textContent="Your learning path could not be loaded. You can still open Learn from the navigation.";
  if(progressResult.status==="fulfilled"&&overviewResult.status==="fulfilled")renderStats(progressResult.value,overviewResult.value);
  if(planResult.status==="fulfilled")renderPlan(planResult.value);else $("#dashboard-plan-preview").replaceChildren(node("p","dashboard-muted","Your saved plan could not be loaded right now."));
  const memTarget=$("#dashboard-memory-preview");if(memTarget){memTarget.replaceChildren();const q=memoryQueueResult.status==="fulfilled"?(memoryQueueResult.value.items||[]):[];if(!q.length){memTarget.append(node("p","dashboard-muted","No cards due right now. Save useful phrases from lessons or feedback."));}else{q.slice(0,2).forEach(item=>{const row=node("div","dashboard-memory-item");row.append(node("span","chip t",item.item_type||"card"),node("strong","",item.front));memTarget.append(row);});if(q.length>2)memTarget.append(node("p","dashboard-muted",(q.length-2)+" more due in Memory."));}}
 }catch(error){$("#dashboard-track-description").textContent=error.message;}finally{loading=false;}
}
function openView(view){window.PreppedApp?.showView(view);}
$("#home-toggle")?.addEventListener("click",()=>openView("dashboard-view"));
$("#practice-toggle")?.addEventListener("click",()=>openView("home-view"));
$("#dashboard-learn-button")?.addEventListener("click",()=>$("#learning-toggle")?.click());
$("#dashboard-refresh")?.addEventListener("click",loadDashboard);
$("#dashboard-path-link")?.addEventListener("click",()=>$("#learning-toggle")?.click());
$("#dashboard-practice-button")?.addEventListener("click",()=>openView("home-view"));
$("#dashboard-progress-link")?.addEventListener("click",()=>{window.PreppedApp?.showView("progress-view");window.PreppedUI?.setProgressTab?.("plan");});
$("#dashboard-memory-link")?.addEventListener("click",()=>$("#memory-toggle")?.click());
function updateNavigation(view){
 const active=view==="dashboard-view"?"home-toggle":view==="learning-view"?"learning-toggle":view==="memory-view"?"memory-toggle":view==="career-view"?"career-toggle":view==="progress-view"?"progress-toggle":view==="profile-view"?"profile-nav-toggle":view==="history-view"?"history-toggle":["home-view","practice-view","feedback-view"].includes(view)?"practice-toggle":null;
 for(const id of ["home-toggle","learning-toggle","practice-toggle","career-toggle","memory-toggle","progress-toggle","profile-nav-toggle","history-toggle"]){const button=$("#"+id);if(!button)continue;button.classList.toggle("is-active",id===active);if(id===active)button.setAttribute("aria-current","page");else button.removeAttribute("aria-current");}
}
window.addEventListener("prepped:viewchange",event=>{
 const view=event.detail?.view;
 if(view!=="dashboard-view")$("#dashboard-view")?.classList.add("hidden");
 updateNavigation(view);
});
window.addEventListener("prepped:navigation",event=>{
 const view=event.detail?.view;
 updateNavigation(view);
 if(view==="dashboard-view"){ $("#dashboard-view")?.classList.remove("hidden");loadDashboard(); }
});
loadDashboard();window.PreppedDashboard={refresh:loadDashboard};
})();