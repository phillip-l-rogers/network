const csrftoken = document.querySelector('meta[name="csrf-token"]').content;

document.addEventListener("DOMContentLoaded", () => {
  // Edit buttons
  document.querySelectorAll(".edit-button").forEach((button) => {
    attachEditListener(button);
  });
  // Like buttons
  document.querySelectorAll(".like-button").forEach((button) => {
    attachLikeListener(button);
  });
});

function attachEditListener(editButton) {
  editButton.addEventListener("click", () => {
    const postId = editButton.dataset.postId;
    const origText = editButton.dataset.postText;
    const postCard = document.querySelector(`#post-${postId}`);
    // Hide the edit button while editing
    editButton.style.display = "none";
    // Create textarea
    const textarea = document.createElement("textarea");
    textarea.className = "form-control";
    textarea.value = origText;
    // Create save button
    const saveButton = document.createElement("button");
    saveButton.className = "btn btn-sm btn-primary mt-2";
    saveButton.textContent = "Save";
    // Replace paragraph with textarea and append save button
    postCard.replaceWith(textarea);
    editButton.parentNode.insertBefore(saveButton, editButton);
    attachSaveListener(saveButton, editButton, textarea);
  });
}

function attachLikeListener(likeButton) {
  likeButton.addEventListener("click", () => {
    const postId = likeButton.dataset.postId;
    // Disable button to prevent double clicks
    likeButton.disabled = true;
    fetch(`/like/${postId}`, {
      method: "PUT",
      headers: {
        "X-CSRFToken": csrftoken,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          alert(data.error);
        } else {
          // Update like button symbol and count
          const heart = data.liked ? "❤️" : "♡";
          likeButton.innerText = `${heart} ${data.num_likes}`;
          likeButton.classList.toggle("liked", data.liked);
        }
      })
      .catch((error) => {
        console.error("Error:", error);
      })
      .finally(() => {
        // Enable button to allow clicks again
        likeButton.disabled = false;
      });
  });
}

function attachSaveListener(saveButton, editButton, textarea) {
  const postId = editButton.dataset.postId;
  // Handle save action
  saveButton.addEventListener("click", () => {
    fetch(`/edit/${postId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify({ text: textarea.value.trim() }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          alert(data.error);
          return;
        }
        // Replace textarea with updated <p>
        const newParagraph = document.createElement("p");
        newParagraph.className = "card-text";
        newParagraph.id = `post-${postId}`;
        newParagraph.innerText = data.new_text;
        const postEditedCard = document.querySelector(`#post-edited-${postId}`);
        if (data.was_edited) {
          postEditedCard.innerText = "(edited)";
        } else {
          postEditedCard.innerText = "";
        }
        saveButton.remove();
        textarea.replaceWith(newParagraph);
        editButton.dataset.postText = data.new_text;
        editButton.style.display = "inline-block";
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("Something went wrong.");
      });
  });
}

function insertPostCard(data) {
  const postsContainer = document.querySelector("#posts");
  const newPost = document.createElement("div");
  newPost.className = "card mb-3";
  const postBody = document.createElement("div");
  postBody.className = "card-body";
  // Post text
  const postText1 = document.createElement("p");
  postText1.className = "card-text";
  postText1.id = `post-${data.post_id}`;
  postText1.innerText = data.text;
  // Created date
  const date = new Date(data.created);
  const options = {
    year: "numeric",
    month: "long", // Full month name
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true, // Use 12-hour format with AM/PM
  };
  let created = date
    .toLocaleString("en-US", options)
    .replace("AM", "a.m.")
    .replace("PM", "p.m.");
  const postText2 = document.createElement("small");
  postText2.className = "text-muted";
  postText2.innerText = `${created} by `;
  // User profile link
  const postUser = document.createElement("a");
  postUser.href = `/profile/${data.username}`;
  postUser.innerText = data.username;
  postText2.append(postUser);
  // Edited marker
  const postEdited = document.createElement("small");
  postEdited.className = "text-muted";
  postEdited.id = `post-edited-${data.post_id}`;
  postText2.append(postEdited);
  // Like + edit buttons
  const postLikeDiv = document.createElement("div");
  postLikeDiv.className = "mt-2";
  // Like button
  const postLike = document.createElement("button");
  postLike.className = "btn btn-sm like-button disabled";
  postLike.disabled = true;
  postLike.setAttribute("aria-disabled", "true");
  postLike.title = "You can't like your own posts.";
  postLike.innerText = "♡ 0";
  attachLikeListener(postLike);
  // Edit button
  const postEdit = document.createElement("button");
  postEdit.className = "btn btn-sm btn-outline-secondary edit-button";
  postEdit.dataset.postId = data.post_id;
  postEdit.dataset.postText = data.text;
  postEdit.innerText = "✏️ Edit";
  attachLikeListener(postEdit);
  postLikeDiv.append(postLike, postEdit);
  postBody.append(postText1, postText2, postLikeDiv);
  newPost.append(postBody);
  postsContainer.prepend(newPost);
  setTimeout(() => newPost.classList.add("visible"), 50);
  // Remove "no posts yet" placeholder if present
  const emptyMessage = postsContainer.querySelector(".empty-post");
  if (emptyMessage) {
    emptyMessage.remove();
  }
  // Hide the compose form after submitting
  const composeButton = document.querySelector("#compose-button");
  const composeForm = document.querySelector("#compose-form");
  const postTextarea = document.querySelector("#new-post-text");
  composeForm.classList.remove("show");
  composeForm.classList.add("d-none");
  composeButton.setAttribute("aria-expanded", false);
  postTextarea.value = "";
}
