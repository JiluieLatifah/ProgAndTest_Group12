document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("contactForm");
    const msg  = document.getElementById("msg");

    if (!form || !msg) return;

    form.addEventListener("submit", function (e) {
        e.preventDefault(); // chặn reload

        const formData  = new FormData(form);
        const contactId = formData.get("id"); // có id => edit

        // Xác định API
        const url = contactId
            ? "/api/contact/edit"
            : "/api/contact/add";

        fetch(url, {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {

                msg.style.color = "lightgreen";
                msg.style.fontWeight = "500";

                msg.innerText = contactId
                    ? "✔ Contact updated successfully"
                    : "✔ Contact added successfully";

                if (!contactId) {
                    form.reset(); // chỉ reset khi add
                }

            } else {
                msg.style.color = "red";
                msg.innerText = data.message || "✖ Operation failed";
            }
        })
        .catch(() => {
            msg.style.color = "red";
            msg.innerText = "✖ Server error";
        });
    });
});
