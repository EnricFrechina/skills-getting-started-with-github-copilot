document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Reset activity select (keep placeholder)
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-section">
            <strong>Current Participants:</strong>
            <ul class="participants-list"></ul>
          </div>
        `;

        activitiesList.appendChild(activityCard);

        const ul = activityCard.querySelector('.participants-list');

        if (!details.participants || details.participants.length === 0) {
          const li = document.createElement('li');
          const em = document.createElement('em');
          em.textContent = 'No participants yet';
          li.appendChild(em);
          ul.appendChild(li);
        } else {
          details.participants.forEach(p => {
            const li = document.createElement('li');
            const span = document.createElement('span');
            span.className = 'participant-email';
            span.textContent = p;
            const btn = document.createElement('button');
            btn.className = 'remove-btn';
            btn.title = 'Unregister';
            btn.setAttribute('data-activity', name);
            btn.setAttribute('data-email', p);
            btn.textContent = '✖';
            li.appendChild(span);
            li.appendChild(btn);
            ul.appendChild(li);
          });
        }

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle clicks on unregister (event delegation)
  activitiesList.addEventListener('click', async (event) => {
    const target = event.target;
    if (target.classList.contains('remove-btn')) {
      const activity = target.getAttribute('data-activity');
      const email = target.getAttribute('data-email');

      if (!confirm(`Unregister ${email} from ${activity}?`)) return;

      try {
        const response = await fetch(
          `/activities/${encodeURIComponent(activity)}/participants?email=${encodeURIComponent(email)}`,
          { method: 'DELETE' }
        );

        const result = await response.json();

        if (response.ok) {
          messageDiv.textContent = result.message;
          messageDiv.className = 'success';
          // Refresh the activities list to reflect removal
          fetchActivities();
        } else {
          messageDiv.textContent = result.detail || 'Failed to unregister participant';
          messageDiv.className = 'error';
        }

        messageDiv.classList.remove('hidden');
        setTimeout(() => {
          messageDiv.classList.add('hidden');
        }, 5000);
      } catch (err) {
        messageDiv.textContent = 'Failed to unregister. Please try again.';
        messageDiv.className = 'error';
        messageDiv.classList.remove('hidden');
        console.error('Error unregistering:', err);
      }
    }
  });

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        // Refresh activities list to show new participant
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
