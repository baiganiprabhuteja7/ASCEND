const STORAGE_KEY = 'skills-to-impact.workspace.v1'

export function loadWorkspace() {
  const saved = window.localStorage.getItem(STORAGE_KEY)
  if (!saved) return { goals: [], tasks: [] }

  const workspace = JSON.parse(saved)
  if (!Array.isArray(workspace.goals) || !Array.isArray(workspace.tasks)) {
    throw new Error('Saved Skills to Impact data is invalid. Clear the app storage to continue.')
  }
  return workspace
}

export function saveWorkspace(workspace) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(workspace))
}
