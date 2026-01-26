document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("groupForm");
    const msg = document.getElementById("groupMsg");
const groupId = document.getElementById("groupContainer").dataset.groupId;

    if (!form) return;

    form.addEventListener("submit", function (e) {
        e.preventDefault(); //  VERY IMPORTANT

        const formData = new FormData(form);

        fetch("/api/group/add", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                msg.style.color = "lightgreen";
                msg.innerText = "Group added successfully!";
                form.reset();
            } else {
                msg.style.color = "red";
                msg.innerText = "Failed to add group";
            }
        })
        .catch(() => {
            msg.style.color = "red";
            msg.innerText = "Server error";
            const url = groupId
        });
    });
});
