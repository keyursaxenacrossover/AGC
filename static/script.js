document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const chatWindow = document.getElementById("chat-window");
    const fileInput = document.getElementById("file-input");
    const imagePreview = document.getElementById("image-preview");
    const loadingOverlay = document.createElement("div");

    // Add a loading overlay element
    loadingOverlay.id = "loading-overlay";
    loadingOverlay.style.display = "none"; // Initially hidden
    loadingOverlay.innerHTML = "<p>Processing...</p>";
    document.body.appendChild(loadingOverlay);

    // Function to toggle interaction
    function toggleInteraction(disable) {
        const inputs = chatForm.querySelectorAll("input, textarea, button");
        inputs.forEach(input => (input.disabled = disable));
        loadingOverlay.style.display = disable ? "flex" : "none";
    }

    // Function to append a message to the chat window
    function appendMessage(role, content) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `chat-message ${role}`;

        // Use Marked.js to render Markdown
        if (role === "bot") {
            messageDiv.innerHTML = marked.parse(content); // Parse Markdown for bot responses
        } else {
            messageDiv.innerHTML = `<p>${content}</p>`; // Keep plain text for user input
        }

        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Handle image preview
    fileInput.addEventListener("change", () => {
        imagePreview.innerHTML = ""; // Clear existing previews
        Array.from(fileInput.files).forEach((file, index) => {
            if (file.type.startsWith("image/")) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const imgDiv = document.createElement("div");
                    imgDiv.className = "image-item";
                    imgDiv.innerHTML = `
                        <img src="${e.target.result}" alt="Preview">
                        <button type="button" onclick="removeFile(${index})">X</button>
                    `;
                    imagePreview.appendChild(imgDiv);
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Function to remove a file
    window.removeFile = (index) => {
        const files = Array.from(fileInput.files);
        files.splice(index, 1);

        const newFileList = new DataTransfer();
        files.forEach(file => newFileList.items.add(file));
        fileInput.files = newFileList.files;

        fileInput.dispatchEvent(new Event("change"));
    };

    // Handle form submission
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();

        const userInput = document.getElementById("user-text").value.trim();
        if (!userInput) {
            alert("Please type a message.");
            return;
        }

        const formData = new FormData(chatForm);

        // Append user's message to the chat
        appendMessage("user", `<p>${userInput}</p>`);

        // Disable inputs and show loading overlay while processing
        toggleInteraction(true);

        fetch("/process", {
            method: "POST",
            body: formData,
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    appendMessage("bot", `<p class="error">${data.error}</p>`);
                } else {
                    appendMessage("bot", data.response); // Markdown will be rendered
                }
            })
            .catch((error) => {
                console.error("Error:", error);
                appendMessage("bot", `<p class="error">An error occurred.</p>`);
            })
            .finally(() => {
                // Re-enable inputs and hide loading overlay
                toggleInteraction(false);
                chatForm.reset();
                imagePreview.innerHTML = ""; // Clear image previews
            });
    });
});
