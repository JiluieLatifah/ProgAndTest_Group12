document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("groupForm");
    const msg = document.getElementById("groupMsg");
    const container = document.getElementById("groupContainer");
    
    // Lấy Group ID từ attribute data-group-id của container (nếu có)
    const groupId = container ? container.dataset.groupId : "";

    if (!form) return;

    // 1. XỬ LÝ SUBMIT FORM (Cho cả Add và Edit)
    form.addEventListener("submit", function (e) {
        e.preventDefault();

        const formData = new FormData(form);
        
        // Nếu có groupId thì gọi API edit, ngược lại gọi API add
        const url = groupId ? "/api/group/edit" : "/api/group/add";

        // Hiển thị trạng thái đang xử lý
        msg.style.color = "yellow";
        msg.innerText = "Đang xử lý...";

        fetch(url, {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                msg.style.color = "lightgreen";
                msg.innerText = data.message;
                
                // Nếu là thêm mới thì reset form, nếu là edit thì giữ nguyên
                if (!groupId) {
                    form.reset();
                }

                // Tự động load lại trang sau 1.5 giây để cập nhật danh sách thành viên mới
                setTimeout(() => {
                    if (groupId) {
                        window.location.reload();
                    } else {
                        window.location.href = "/groups";
                    }
                }, 1500);

            } else {
                msg.style.color = "red";
                msg.innerText = "Lỗi: " + data.message;
            }
        })
        .catch((error) => {
            console.error("Error:", error);
            msg.style.color = "red";
            msg.innerText = "Lỗi kết nối Server!";
        });
    });
});

// 2. HÀM XÓA THÀNH VIÊN KHỎI NHÓM (Dùng cho nút Remove trong danh sách thành viên)
function removeMember(groupId, contactId, btnElement) {
    if (!confirm("Bạn có chắc muốn xóa liên hệ này khỏi nhóm?")) return;

    // Hiển thị trạng thái đang xóa trên nút
    const originalText = btnElement.innerText;
    btnElement.innerText = "...";
    btnElement.disabled = true;

    fetch(`/api/group/${groupId}/remove_member/${contactId}`, {
        method: "POST"
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            // Xóa dòng đó trên giao diện ngay lập tức mà không cần reload
            const row = btnElement.parentElement;
            row.style.opacity = '0';
            setTimeout(() => {
                row.remove();
                
                // Nếu không còn thành viên nào, hiện thông báo trống
                const memberList = document.getElementById('memberList');
                if (memberList && memberList.querySelectorAll('.member-item').length === 0) {
                    memberList.innerHTML = '<p style="color: #888; text-align: center; padding: 10px;">Nhóm này chưa có thành viên.</p>';
                }
            }, 300);
        } else {
            alert("Lỗi: " + data.message);
            btnElement.innerText = originalText;
            btnElement.disabled = false;
        }
    })
    .catch(() => {
        alert("Server error!");
        btnElement.innerText = originalText;
        btnElement.disabled = false;
    });
}
