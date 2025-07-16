document.addEventListener("DOMContentLoaded", () => {
  // Follow button
  const button = document.querySelector(".follow-button");
  if (button) {
    attachFollowListener(button);
  }
});

function attachFollowListener(followButton) {
  followButton.addEventListener("click", () => {
    const username = followButton.dataset.username;
    const isFollowing =
      String(followButton.dataset.following).toLowerCase() === "true";
    const method = isFollowing ? "DELETE" : "POST";
    // Disable button to prevent double clicks
    followButton.disabled = true;
    fetch(`/follow/${username}`, {
      method: method,
      headers: {
        "X-CSRFToken": csrftoken,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          alert(data.error);
        } else {
          // Update follower button text and count
          const numFollowers = data.num_followers;
          const followerLabel = numFollowers === 1 ? "follower" : "followers";
          followButton.textContent = data.following ? "Unfollow" : "Follow";
          followButton.classList.toggle("btn-danger");
          followButton.classList.toggle("btn-primary");
          followButton.dataset.following = data.following.toString();
          document.querySelector("#num_followers").textContent =
            `${numFollowers} ${followerLabel}`;
        }
      })
      .catch((error) => {
        console.error("Error:", error);
      })
      .finally(() => {
        // Enable button to allow clicks again
        followButton.disabled = false;
      });
  });
}
