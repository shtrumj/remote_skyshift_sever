// Main JavaScript for Remote Agent Manager

// Global variables
let refreshInterval = null;
let isConnected = true;

// Initialize when document is ready
$(document).ready(function () {
  initializeApp();
});

// Initialize the application
function initializeApp() {
  console.log("🚀 Remote Agent Manager initialized");

  // Start auto-refresh
  startAutoRefresh();

  // Setup connection monitoring
  setupConnectionMonitoring();

  // Setup keyboard shortcuts
  setupKeyboardShortcuts();

  // Load current user information
  console.log("🔍 About to call loadCurrentUser()");
  loadCurrentUser();
  console.log("🔍 loadCurrentUser() called");
}

// Start auto-refresh functionality
function startAutoRefresh() {
  // Refresh every 10 seconds
  refreshInterval = setInterval(function () {
    if (isConnected) {
      // Only call loadAgents if it exists (dashboard pages)
      if (typeof loadAgents === "function") {
        loadAgents();
      }
      // For admin dashboard, refresh admin data
      if (
        typeof AdminDashboard !== "undefined" &&
        typeof AdminDashboard.loadAdminDashboard === "function"
      ) {
        AdminDashboard.loadAdminDashboard();
      }
    }
  }, 10000);
}

// Setup connection monitoring
function setupConnectionMonitoring() {
  // Monitor connection status
  $(document).ajaxError(function (event, xhr, settings) {
    if (xhr.status === 0 || xhr.status >= 500) {
      updateConnectionStatus(false);
    }
  });

  $(document).ajaxSuccess(function (event, xhr, settings) {
    updateConnectionStatus(true);
  });
}

// Update connection status display
function updateConnectionStatus(connected) {
  isConnected = connected;
  const statusElement = $("#connection-status");
  const iconElement = statusElement.prev("i");

  if (connected) {
    statusElement
      .text("Connected")
      .removeClass("text-danger")
      .addClass("text-success");
    iconElement.removeClass("text-danger").addClass("text-success");
  } else {
    statusElement
      .text("Disconnected")
      .removeClass("text-success")
      .addClass("text-danger");
    iconElement.removeClass("text-success").addClass("text-danger");
  }
}

// Setup keyboard shortcuts
function setupKeyboardShortcuts() {
  $(document).keydown(function (e) {
    // Ctrl+R to refresh
    if (e.ctrlKey && e.key === "r") {
      e.preventDefault();
      if (typeof refreshAgents === "function") {
        refreshAgents();
      } else {
        location.reload();
      }
    }

    // Escape to hide command panel
    if (e.key === "Escape") {
      hideCommandPanel();
    }

    // Ctrl+Enter to submit command
    if (e.ctrlKey && e.key === "Enter") {
      if ($("#command-form").is(":visible")) {
        $("#command-form").submit();
      }
    }
  });
}

// Show notification
function showNotification(message, type = "info") {
  const alertClass = `alert-${type}`;
  const icon =
    type === "success"
      ? "check-circle"
      : type === "error"
      ? "exclamation-triangle"
      : type === "warning"
      ? "exclamation-triangle"
      : "info-circle";

  const notification = `
        <div class="alert ${alertClass} alert-dismissible fade show position-fixed" style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;" role="alert">
            <i class="fas fa-${icon} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

  // Remove existing notifications
  $(".alert.position-fixed").remove();

  // Add to page
  $("body").append(notification);

  // Auto-dismiss after 5 seconds
  setTimeout(function () {
    $(".alert.position-fixed").fadeOut();
  }, 5000);
}

// Format timestamp
function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;

  if (diff < 60000) {
    // Less than 1 minute
    return "Just now";
  } else if (diff < 3600000) {
    // Less than 1 hour
    const minutes = Math.floor(diff / 60000);
    return `${minutes} minute${minutes > 1 ? "s" : ""} ago`;
  } else if (diff < 86400000) {
    // Less than 1 day
    const hours = Math.floor(diff / 3600000);
    return `${hours} hour${hours > 1 ? "s" : ""} ago`;
  } else {
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  }
}

// Copy to clipboard
function copyToClipboard(text) {
  navigator.clipboard
    .writeText(text)
    .then(function () {
      showNotification("Copied to clipboard!", "success");
    })
    .catch(function () {
      showNotification("Failed to copy to clipboard", "error");
    });
}

// Export agents data
function exportAgentsData() {
  $.get("/api/agents", function (data) {
    const exportData = {
      timestamp: new Date().toISOString(),
      agents: data.agents,
      summary: {
        total: data.total,
        online: data.online,
        offline: data.offline,
      },
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `agents-export-${new Date().toISOString().split("T")[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showNotification("Agents data exported successfully!", "success");
  });
}

// Show agent details modal
function showAgentDetails(agentId) {
  $.get(`/api/agents/${agentId}`, function (agent) {
    const modal = `
            <div class="modal fade" id="agentDetailsModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-server me-2"></i>
                                Agent Details
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <strong>Hostname:</strong><br>
                                    <span class="text-primary">${
                                      agent.hostname
                                    }</span>
                                </div>
                                <div class="col-md-6">
                                    <strong>Status:</strong><br>
                                    <span class="badge bg-${
                                      agent.status === "online"
                                        ? "success"
                                        : "secondary"
                                    }">${agent.status}</span>
                                </div>
                            </div>
                            <hr>
                            <div class="row">
                                <div class="col-md-6">
                                    <strong>IP Address:</strong><br>
                                    <code>${agent.ip_address}</code>
                                </div>
                                <div class="col-md-6">
                                    <strong>Port:</strong><br>
                                    <code>${agent.port}</code>
                                </div>
                            </div>
                            <hr>
                            <div class="row">
                                <div class="col-12">
                                    <strong>Capabilities:</strong><br>
                                    ${agent.capabilities
                                      .map(
                                        (cap) =>
                                          `<span class="badge bg-info me-1">${cap}</span>`
                                      )
                                      .join("")}
                                </div>
                            </div>
                            <hr>
                            <div class="row">
                                <div class="col-md-6">
                                    <strong>Version:</strong><br>
                                    <code>${agent.version}</code>
                                </div>
                                <div class="col-md-6">
                                    <strong>Registered:</strong><br>
                                    <small class="text-muted">${formatTimestamp(
                                      agent.registered_at
                                    )}</small>
                                </div>
                            </div>
                            <hr>
                            <div class="row">
                                <div class="col-12">
                                    <strong>Last Heartbeat:</strong><br>
                                    <small class="text-muted">${formatTimestamp(
                                      agent.last_heartbeat
                                    )}</small>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="selectAgent('${
                              agent.agent_id
                            }', '${agent.hostname}')" data-bs-dismiss="modal">
                                <i class="fas fa-terminal me-2"></i>
                                Send Command
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

    // Remove existing modal if any
    $("#agentDetailsModal").remove();

    // Add new modal
    $("body").append(modal);

    // Show modal
    $("#agentDetailsModal").modal("show");
  });
}

// Utility function to debounce
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Debounced refresh function
const debouncedRefresh = debounce(function () {
  if (typeof refreshAgents === "function") {
    refreshAgents();
  } else {
    // Fallback: reload the page if refreshAgents is not available
    location.reload();
  }
}, 1000);

// Add right-click context menu for agents
$(document).on("contextmenu", ".agent-row", function (e) {
  e.preventDefault();
  const agentId = $(this).data("agent-id");
  const hostname = $(this).find("td:nth-child(2) strong").text();

  const contextMenu = `
        <div class="dropdown-menu show" style="position: fixed; left: ${e.pageX}px; top: ${e.pageY}px;">
            <a class="dropdown-item" href="#" onclick="showAgentDetails('${agentId}')">
                <i class="fas fa-info-circle me-2"></i>
                View Details
            </a>
            <a class="dropdown-item" href="#" onclick="selectAgent('${agentId}', '${hostname}')">
                <i class="fas fa-terminal me-2"></i>
                Send Command
            </a>
            <div class="dropdown-divider"></div>
            <a class="dropdown-item" href="#" onclick="copyToClipboard('${agentId}')">
                <i class="fas fa-copy me-2"></i>
                Copy Agent ID
            </a>
        </div>
    `;

  // Remove existing context menus
  $(".dropdown-menu.show").remove();

  // Add new context menu
  $("body").append(contextMenu);

  // Hide context menu when clicking elsewhere
  $(document).one("click", function () {
    $(".dropdown-menu.show").remove();
  });
});

// Load current user information
function loadCurrentUser() {
  console.log("🔍 loadCurrentUser() called");
  console.log("🔍 Making AJAX request to /api/users/profile");

  $.ajax({
    url: "/api/users/profile",
    method: "GET",
    xhrFields: {
      withCredentials: true,
    },
    success: function (user) {
      console.log("✅ AJAX success - user data:", user);

      // Update the current user display in the navigation
      $("#current-user").text(user.username);
      console.log(`👤 Updated current user display to: ${user.username}`);

      // Also update the page title if it's generic
      if (document.title === "Remote Agent Manager") {
        document.title = `Remote Agent Manager - ${user.username}`;
      }

      // Show admin link if user is admin
      if (user.is_admin) {
        $("#admin-nav-item").show();
        console.log("👑 Showing admin nav item");
      }

      console.log(`👤 Current user loaded: ${user.username}`);
    },
    error: function (xhr, status, error) {
      console.log("❌ AJAX error - status:", xhr.status);
      console.log("❌ AJAX error - status text:", xhr.statusText);
      console.log("❌ AJAX error - response:", xhr.responseText);
      console.log("❌ AJAX error - error:", error);

      // If not authenticated, redirect to login
      if (xhr.status === 401) {
        console.log("🔒 User not authenticated, redirecting to login");
        window.location.href = "/ui/login";
      } else {
        console.log("⚠️ Failed to load current user:", xhr.status);
        // Keep showing "User" as fallback
      }
    },
  });
}

// Console logging for debugging
console.log("📡 Remote Agent Manager JavaScript loaded");
