async function loadDashboard() {
    const res = await fetch("/dashboard_data");
    if (!res.ok) {
        window.location.href = "login.html";
        return;
    }

    const data = await res.json();

    document.getElementById("monthlyIncome").innerText = `$${data.income}`;
    document.getElementById("totalExpenses").innerText = `$${data.expenses}`;
    document.getElementById("netSavings").innerText = `$${data.savings}`;
    document.getElementById("savingsRate").innerText = `${data.savings_rate}%`;

    const table = document.getElementById("recentExpensesTable");
    table.innerHTML = "";

    data.recent_expenses.forEach(exp => {
        table.innerHTML += `
            <tr>
                <td>${exp.description}</td>
                <td>${exp.category}</td>
                <td>$${exp.amount}</td>
                <td>${exp.date}</td>
            </tr>
        `;
    });
}

loadDashboard();
