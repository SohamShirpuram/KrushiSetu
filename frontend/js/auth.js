/**
 * KrushiSetu - Authentication and Onboarding Handlers
 */

document.addEventListener("DOMContentLoaded", () => {
  // Login form handler
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    initLoginForm(loginForm);
  }

  // Register form handler
  const registerForm = document.getElementById("registerForm");
  if (registerForm) {
    initRegisterForm(registerForm);
  }

  // Check URL params for feedback alerts
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("expired")) {
    showAlert("Your session has expired. Please log in again.", "danger");
  }
});

function showAlert(message, type = "danger") {
  const alertBox = document.getElementById("alertBox");
  if (alertBox) {
    alertBox.textContent = message;
    alertBox.className = `alert-box ${type}`;
    alertBox.style.display = "block";
  }
}

function clearAlert() {
  const alertBox = document.getElementById("alertBox");
  if (alertBox) {
    alertBox.style.display = "none";
  }
}

function initLoginForm(form) {
  // Set up demo role quick-fill chips
  document.querySelectorAll(".demo-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const username = chip.getAttribute("data-user");
      const usernameInput = document.getElementById("username");
      const passwordInput = document.getElementById("password");
      if (usernameInput && passwordInput) {
        usernameInput.value = username;
        passwordInput.value = "Krushi@123";
        clearAlert();
      }
    });
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearAlert();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const submitBtn = form.querySelector("button[type='submit']");

    if (!username || !password) {
      showAlert("Please enter both username and password.");
      return;
    }

    try {
      submitBtn.disabled = true;
      submitBtn.textContent = "Authenticating...";

      const response = await ApiClient.login(username, password);
      if (response && response.access_token) {
        showAlert("Login successful! Redirecting...", "success");
        setTimeout(() => {
          window.location.href = "/pages/dashboard.html";
        }, 600);
      }
    } catch (err) {
      showAlert(err.message || "Login failed. Please check your credentials.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Sign In to Portal";
    }
  });
}

function initRegisterForm(form) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearAlert();

    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const role = document.getElementById("role").value;
    const full_name = document.getElementById("full_name").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const jurisdiction_or_location = document.getElementById("location").value.trim();
    const submitBtn = form.querySelector("button[type='submit']");

    if (!username || !email || !password || !role || !full_name) {
      showAlert("Please fill in all required fields.");
      return;
    }

    try {
      submitBtn.disabled = true;
      submitBtn.textContent = "Registering...";

      const response = await ApiClient.register({
        username,
        email,
        password,
        role,
        full_name,
        phone,
        jurisdiction_or_location,
      });

      let idMsg = "";
      if (response.farmer_id) {
        idMsg = ` Your unique Farmer ID is: ${response.farmer_id}.`;
      } else if (response.buyer_id) {
        idMsg = ` Your unique Bulk Buyer ID is: ${response.buyer_id}.`;
      }

      showAlert(`Registration successful!${idMsg} Redirecting to login...`, "success");
      setTimeout(() => {
        window.location.href = "/pages/login.html";
      }, 1500);
    } catch (err) {
      showAlert(err.message || "Registration failed. Please review the details.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Create Account";
    }
  });
}

function logout() {
  ApiClient.removeToken();
  window.location.href = "/pages/login.html";
}

window.logout = logout;

