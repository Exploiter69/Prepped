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
 visible.forEach((lesson,index)=>{const done=completed.has(lesson.id),row=node("article","dashboard-lesson"+(done?" is-complete":"")),marker=node("span","dashboard-lesson-marker",done?"✓":String(index+1)),copy=node("div");marker.setAttribute("aria-hidden","true");copy.append(node("h3","",lesson.title),node("p","",lesson.summary||"A short guided practice session."));row.append(marker,copy,node("span","dashboard-lesson-status",done?"COMPLETED":(lesson.estimated_minutes||8)+" MIN"));target.append(row);});
 if(!visible.length)target.append(node("p","dashboard-muted","No lessons are available in this path yet."));
}
function renderPlan(result){
 const target=$("#dashboard-plan-preview");target.replaceChildren();const items=result.plan?.items||[];
 if(!items.length){target.append(node("p","dashboard-muted","No plan has been created for today. Your learning path is ready whenever you are."));return;}
 items.slice(0,4).forEach((item,index)=>{const row=node("div","dashboard-plan-item"),copy=node("div");row.append(node("span","",item.status==="completed"?"✓":String(index+1)));copy.append(node("strong","",item.title),node("small","",(item.estimated_minutes||0)+" min · "+String(item.status||"planned").replaceAll("_"," ")));row.append(copy);target.append(row);});
 if(items.length>4)target.append(node("p","dashboard-muted",(items.length-4)+" more activities in your plan."));
}
function renderStats(progress,overview){$("#dashboard-lessons-completed").textContent=String(progress.lessons_completed??0);$("#dashboard-skills-active").textContent=String(overview.summary?.skills_with_activity??0);$("#dashboard-reviews-due").textContent=String(overview.summary?.due_memory_items??0);}
async function loadDashboard(){
 if(loading)return;loading=true;
 try{
  const results=await Promise.allSettled([request("/api/profile"),request("/api/learning/catalog"),request("/api/learning/progress"),request("/api/intelligence/overview"),request("/api/intelligence/plan?plan_date="+encodeURIComponent(localDate()))]);
  const [profileResult,catalogResult,progressResult,overviewResult,planResult]=results;
  if(profileResult.status==="fulfilled"){const profile=profileResult.value.profile,name=profile?.display_name?.trim();$("#dashboard-greeting").textContent=name?"WELCOME BACK, "+name.toUpperCase():"YOUR NEXT SMALL STEP";const labels={english_fluency:"Build confidence and fluency in everyday English.",placement_interviews:"Prepare to communicate clearly in placement conversations.",technical_interviews:"Practise explaining technical ideas with clarity.",project_communication:"Get better at explaining the work you do.",professional_communication:"Build clear, confident professional communication."};if(profile?.primary_goal)$("#dashboard-goal").textContent=labels[profile.primary_goal]||"Build the communication skills you want, at your own pace.";}
  if(catalogResult.status==="fulfilled"&&progressResult.status==="fulfilled")renderPath(catalogResult.value,progressResult.value);else $("#dashboard-track-description").textContent="Your learning path could not be loaded. You can still open Learn from the navigation.";
  if(progressResult.status==="fulfilled"&&overviewResult.status==="fulfilled")renderStats(progressResult.value,overviewResult.value);
  if(planResult.status==="fulfilled")renderPlan(planResult.value);else $("#dashboard-plan-preview").replaceChildren(node("p","dashboard-muted","Your saved plan could not be loaded right now."));
 }catch(error){$("#dashboard-track-description").textContent=error.message;}finally{loading=false;}
}
function openView(view){window.PreppedApp?.showView(view);}
$("#home-toggle")?.addEventListener("click",()=>openView("dashboard-view"));
$("#practice-toggle")?.addEventListener("click",()=>openView("home-view"));
$("#dashboard-learn-button")?.addEventListener("click",()=>$("#learning-toggle")?.click());
$("#dashboard-path-link")?.addEventListener("click",()=>$("#learning-toggle")?.click());
$("#dashboard-practice-button")?.addEventListener("click",()=>openView("home-view"));
$("#dashboard-progress-link")?.addEventListener("click",()=>$("#progress-toggle")?.click());
function updateNavigation(view){
 const active=view==="dashboard-view"?"home-toggle":view==="learning-view"?"learning-toggle":view==="career-view"?"career-toggle":view==="progress-view"?"progress-toggle":view==="history-view"?"history-toggle":["home-view","practice-view","feedback-view"].includes(view)?"practice-toggle":null;
 for(const id of ["home-toggle","learning-toggle","practice-toggle","career-toggle","progress-toggle","history-toggle"]){const button=$("#"+id);if(!button)continue;button.classList.toggle("is-active",id===active);if(id===active)button.setAttribute("aria-current","page");else button.removeAttribute("aria-current");}
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