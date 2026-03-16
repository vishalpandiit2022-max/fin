document.getElementById("getAdviceButton")?.addEventListener("click", async () => {
    const body = {
        total_savings: document.getElementById("advisoryTotalSavings").value,
        goals: document.getElementById("advisoryFinancialGoals").value,
        risk: document.getElementById("riskTolerance").value,
        horizon: document.getElementById("investmentTimeHorizon").value
    };

    const res = await fetch("/get_financial_advice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    const data = await res.json();
    document.getElementById("personalizedPlanMessage").innerText = data.advice;
});
