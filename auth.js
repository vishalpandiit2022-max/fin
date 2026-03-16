// ---------- LOGIN ----------
const loginForm = document.getElementById("loginForm");
if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const email = loginForm.email.value;
        const password = loginForm.password.value;

        const res = await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();
        document.getElementById("loginMessage").innerText = data.message;

        if (res.ok) window.location.href = "dashboard.html";
    });
}

// ---------- SIGNUP ----------
const signupForm = document.getElementById("signupForm");
if (signupForm) {
    signupForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const body = {
            fullName: signupForm.fullName.value,
            email: signupForm.email.value,
            password: signupForm.password.value,
            monthlySalary: signupForm.monthlySalary.value
        };

        const res = await fetch("/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        const data = await res.json();
        document.getElementById("signupMessage").innerText = data.message;

        if (res.ok) window.location.href = "login.html";
    });
}

// ---------- LOGOUT ----------
document.querySelectorAll("#logoutButton").forEach(btn => {
    btn.addEventListener("click", async () => {
        await fetch("/logout");
        window.location.href = "login.html";
    });
});
