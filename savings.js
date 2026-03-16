const modal = document.getElementById("goalModal");
const newGoalBtn = document.getElementById("newGoalButton");

if (newGoalBtn) {
    newGoalBtn.onclick = () => modal.style.display = "block";
}

window.onclick = (e) => {
    if (e.target === modal) modal.style.display = "none";
};

async function loadGoals() {
    const res = await fetch("/savings_goals");
    const goals = await res.json();

    const container = document.getElementById("goalsContainer");
    container.innerHTML = "";

    if (goals.length === 0) {
        document.getElementById("noGoalsMessage").style.display = "block";
        return;
    }

    goals.forEach(g => {
        const percent = Math.round((g.saved / g.target) * 100);
        container.innerHTML += `
            <div class="card">
                <h3>${g.goal}</h3>
                <p>$${g.saved} / $${g.target}</p>
                <progress value="${percent}" max="100"></progress>
            </div>
        `;
    });
}

const addGoalForm = document.getElementById("addGoalForm");
if (addGoalForm) {
    addGoalForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const body = {
            goal_name: addGoalForm.goal_name.value,
            target_amount: addGoalForm.target_amount.value,
            months: addGoalForm.months.value
        };

        await fetch("/savings_goals", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        modal.style.display = "none";
        addGoalForm.reset();
        loadGoals();
    });
}

loadGoals();
