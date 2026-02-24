export async function fetchBootstrapConfig() {
  const response = await fetch("/api/config/bootstrap");

  if (!response.ok) {
    throw new Error(`Backend returned HTTP ${response.status}`);
  }

  return response.json();
}
