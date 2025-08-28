export async function fetchFloodInfo(location: string) {
  const res = await fetch(`/api/flood-info?location=${location}`)
  if (!res.ok) throw new Error("Failed to fetch flood info")
  return res.json()
}
