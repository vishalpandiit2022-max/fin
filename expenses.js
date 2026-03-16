async function loadExpenses() {
    const res = await fetch("/expenses");
    if (!res.ok) {
        window.location.href = "login.html";
        return;
    }

    const expenses = await res.json();
    const table = document.getElementById("allExpensesTable");
    table.innerHTML = "";

    expenses.forEach(e => {
        table.innerHTML += `
            <tr>
                <td>${e.description}</td>
                <td>${e.category}</td>
                <td>$${e.amount}</td>
                <td>${e.date}</td>
            </tr>
        `;
    });
}

const addExpenseForm = document.getElementById("addExpenseForm");
if (addExpenseForm) {
    addExpenseForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const body = {
            description: addExpenseForm.description.value,
            category: addExpenseForm.category.value,
            amount: addExpenseForm.amount.value,
            date: addExpenseForm.date.value
        };

        const res = await fetch("/expenses", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        document.getElementById("expenseMessage").innerText =
            res.ok ? "Expense added successfully" : "Failed to add expense";

        addExpenseForm.reset();
        loadExpenses();
    });
}

loadExpenses();
