// Admin Dashboard JavaScript
console.log("🔍 Admin dashboard script loaded");

// Use a different variable name to avoid conflicts
var AdminDashboardManager = {
  // Function to initialize admin dashboard
  init: function () {
    console.log("✅ jQuery available, initializing admin dashboard");

    // Load pending users
    $.ajax({
      url: "/api/admin/pending-users",
      method: "GET",
      xhrFields: { withCredentials: true },
      success: function (data) {
        console.log("✅ Pending users loaded:", data);
        $("#pending-count").text(data.total);

        if (data.pending_users.length === 0) {
          $("#pending-users-container").html(`
                        <div class="text-center py-4">
                            <i class="fas fa-check-circle fa-2x text-success"></i>
                            <p class="mt-2 text-muted">No pending users to approve</p>
                        </div>
                    `);
        } else {
          let html = `
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Username</th>
                                        <th>Email</th>
                                        <th>Full Name</th>
                                        <th>Created</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;

          data.pending_users.forEach((user) => {
            const createdDate = new Date(user.created_at).toLocaleDateString();
            html += `
                            <tr>
                                <td><strong>${user.username}</strong></td>
                                <td>${user.email}</td>
                                <td>${user.full_name || "N/A"}</td>
                                <td>${createdDate}</td>
                                <td>
                                    <button class="btn btn-success btn-sm me-2" onclick="AdminDashboardManager.approveUser('${
                                      user.id
                                    }', '${user.username}')">
                                        <i class="fas fa-check me-1"></i>Approve
                                    </button>
                                    <button class="btn btn-danger btn-sm" onclick="AdminDashboardManager.rejectUser('${
                                      user.id
                                    }', '${user.username}')">
                                        <i class="fas fa-times me-1"></i>Reject
                                    </button>
                                </td>
                            </tr>
                        `;
          });

          html += `
                                </tbody>
                            </table>
                        </div>
                    `;

          $("#pending-users-container").html(html);
        }
      },
      error: function (xhr) {
        console.log("❌ Failed to load pending users:", xhr.status);
        $("#pending-users-container").html(`
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Failed to load pending users: ${xhr.status}
                    </div>
                `);
      },
    });

    // Load all users
    $.ajax({
      url: "/api/users",
      method: "GET",
      xhrFields: { withCredentials: true },
      success: function (data) {
        console.log("✅ All users loaded:", data);
        $("#total-users").text(data.total);

        let adminCount = 0;
        let activeCount = 0;

        data.users.forEach((user) => {
          if (user.is_admin) adminCount++;
          if (user.is_active) activeCount++;
        });

        $("#admin-count").text(adminCount);
        $("#active-count").text(activeCount);

        // Populate the all users table
        if (data.users.length === 0) {
          $("#all-users-container").html(`
                        <div class="text-center py-4">
                            <i class="fas fa-users fa-2x text-muted"></i>
                            <p class="mt-2 text-muted">No users found</p>
                        </div>
                    `);
        } else {
          let html = `
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Username</th>
                                        <th>Email</th>
                                        <th>Full Name</th>
                                        <th>Status</th>
                                        <th>Role</th>
                                        <th>Created</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;

          data.users.forEach((user) => {
            const createdDate = new Date(user.created_at).toLocaleDateString();
            const statusBadge = user.is_active
              ? '<span class="badge bg-success">Active</span>'
              : '<span class="badge bg-danger">Inactive</span>';
            const roleBadge = user.is_admin
              ? '<span class="badge bg-warning">Admin</span>'
              : '<span class="badge bg-secondary">User</span>';
            const approvalBadge = user.is_approved
              ? '<span class="badge bg-success">Approved</span>'
              : '<span class="badge bg-warning">Pending</span>';

            html += `
                            <tr>
                                <td><strong>${user.username}</strong></td>
                                <td>${user.email}</td>
                                <td>${user.full_name || "N/A"}</td>
                                <td>${statusBadge}</td>
                                <td>${roleBadge}</td>
                                <td>${createdDate}</td>
                                <td>
                                    ${
                                      !user.is_approved
                                        ? `
                                        <button class="btn btn-success btn-sm me-1" onclick="AdminDashboardManager.approveUser('${user.id}', '${user.username}')">
                                            <i class="fas fa-check me-1"></i>Approve
                                        </button>
                                        <button class="btn btn-danger btn-sm me-1" onclick="AdminDashboardManager.rejectUser('${user.id}', '${user.username}')">
                                            <i class="fas fa-times me-1"></i>Reject
                                        </button>
                                    `
                                        : ""
                                    }
                                    <button class="btn btn-danger btn-sm" onclick="AdminDashboardManager.deleteUser('${
                                      user.id
                                    }', '${user.username}')">
                                        <i class="fas fa-trash me-1"></i>Delete
                                    </button>
                                </td>
                            </tr>
                        `;
          });

          html += `
                                </tbody>
                            </table>
                        </div>
                    `;

          $("#all-users-container").html(html);
        }
      },
      error: function (xhr) {
        console.log("❌ Failed to load all users:", xhr.status);
        $("#all-users-container").html(`
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Failed to load all users: ${xhr.status}
                    </div>
                `);
      },
    });
  },

  // User action functions
  approveUser: function (userId, username) {
    if (confirm(`Are you sure you want to approve user "${username}"?`)) {
      $.ajax({
        url: `/api/admin/users/${userId}/approve`,
        method: "POST",
        xhrFields: { withCredentials: true },
        success: function (data) {
          alert("User approved successfully!");
          location.reload();
        },
        error: function (xhr) {
          alert(`Failed to approve user: ${xhr.status}`);
        },
      });
    }
  },

  rejectUser: function (userId, username) {
    if (
      confirm(
        `Are you sure you want to reject user "${username}"? This will deactivate their account.`
      )
    ) {
      $.ajax({
        url: `/api/admin/users/${userId}/reject`,
        method: "POST",
        xhrFields: { withCredentials: true },
        success: function (data) {
          alert("User rejected successfully!");
          location.reload();
        },
        error: function (xhr) {
          alert(`Failed to reject user: ${xhr.status}`);
        },
      });
    }
  },

  deleteUser: function (userId, username) {
    if (
      confirm(
        `Are you sure you want to delete user "${username}"? This action cannot be undone.`
      )
    ) {
      $.ajax({
        url: `/api/users/${userId}`,
        method: "DELETE",
        xhrFields: { withCredentials: true },
        success: function (data) {
          alert("User deleted successfully!");
          location.reload();
        },
        error: function (xhr) {
          alert(`Failed to delete user: ${xhr.status}`);
        },
      });
    }
  },

  // Function that main.js expects
  loadAdminDashboard: function () {
    console.log("🔄 Refreshing admin dashboard data...");
    this.init();
  },
};

// Also create the AdminDashboard object for main.js compatibility
var AdminDashboard = {
  loadAdminDashboard: function () {
    console.log("🔄 AdminDashboard.loadAdminDashboard called");
    AdminDashboardManager.loadAdminDashboard();
  },
};

// Wait for jQuery and DOM to be ready
function waitForJQuery() {
  if (typeof $ !== "undefined") {
    console.log("🔍 Admin dashboard document ready");
    AdminDashboardManager.init();
  } else {
    console.log("⏳ jQuery not ready, waiting...");
    setTimeout(waitForJQuery, 100);
  }
}

// Start waiting for jQuery
waitForJQuery();
