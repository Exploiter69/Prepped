const statusElement = document.querySelector("#system-status");
const descriptionElement = document.querySelector("#scenario-description");
const roleElement = document.querySelector("#scenario-role");
const lengthElement = document.querySelector("#scenario-length");
const versionElement = document.querySelector("#scenario-version");
const questionList = document.querySelector("#question-list");

async function loadStarterData() {
  try {
    const [healthResponse, scenarioResponse] = await Promise.all([
      fetch("/api/health"),
      fetch("/api/scenarios/project-explanation"),
    ]);

    if (!healthResponse.ok || !scenarioResponse.ok) {
      throw new Error("The local app could not load its starter data.");
    }

    const health = await healthResponse.json();
    const scenario = await scenarioResponse.json();

    statusElement.textContent = health.status === "ok" ? "Local app ready" : "App status unknown";
    descriptionElement.textContent = scenario.description;
    roleElement.textContent = scenario.role;
    lengthElement.textContent = Number.isFinite(scenario.estimated_minutes)
      ? `About ${scenario.estimated_minutes} minutes`
      : "Not specified";
    versionElement.textContent = scenario.version;

    questionList.replaceChildren();
    for (const question of scenario.questions) {
      const item = document.createElement("li");
      item.textContent = question.prompt;
      questionList.append(item);
    }
  } catch (error) {
    statusElement.textContent = "Could not load local app";
    statusElement.classList.add("error");
    descriptionElement.textContent = error instanceof Error
      ? error.message
      : "Unexpected error loading scenario.";
    questionList.replaceChildren();
  }
}

loadStarterData();
