export async function exampleFunction(params: any): Promise<number> {
    const res = await fetch("/api/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
    });
    return res.json();
}