async function loadProfile() {
    const res = await fetch("/profile_data");
    if (!res.ok) {
        window.location.href = "login.html";
        return;
    }

    const data = await res.json();
    document.getElementById("profileName").innerText = data.name;
    document.getElementById("profileEmail").innerText = data.email;
    document.getElementById("profileSalary").innerText = `$${data.salary}`;
}

const updateSalaryForm = document.getElementById("updateSalaryForm");
if (updateSalaryForm) {
    updateSalaryForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const res = await fetch("/salary", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                new_salary: updateSalaryForm.newMonthlySalary.value
            })
        });

        document.getElementById("profileMessage").innerText =
            res.ok ? "Salary updated" : "Failed to update salary";

        loadProfile();
    });
}

loadProfile();
