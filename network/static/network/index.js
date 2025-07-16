document.addEventListener("DOMContentLoaded", () => {
  // Compose button and forms
  const composeButton = document.querySelector("#compose-button");
  const composeForm = document.querySelector("#compose-form");
  const postForm = document.querySelector("#new-post-form");
  const postTextarea = document.querySelector("#new-post-text");
  if (composeButton && composeForm && postForm && postTextarea) {
    composeButton.addEventListener("click", () => {
      const isVisible = composeForm.classList.contains("show");
      composeForm.classList.toggle("show");
      composeForm.classList.toggle("d-none", isVisible);
      composeButton.setAttribute("aria-expanded", !isVisible);
      if (!isVisible) postTextarea.focus();
    });
    postForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const text = postTextarea.value.trim();
      if (!text) return; // Don't allow blank posts
      // Optional visual feedback on button
      const submitBtn = postForm.querySelector("button[type='submit']");
      submitBtn.disabled = true;
      submitBtn.textContent = "Posting...";
      fetch("/compose", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({ text }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.error) {
            alert(data.error);
          } else {
            insertPostCard(data);
          }
        })
        .catch((error) => console.error("Error composing post:", error))
        .finally(() => {
          submitBtn.disabled = false;
          submitBtn.textContent = "Post";
        });
    });
  }
});
