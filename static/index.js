document
  .getElementById("fetchMetadataButton")
  .addEventListener("click", function () {
    const url = document.getElementById("urlInput").value;
    if (!url) {
      showAlert("Please enter a URL.", "error");
      return;
    }

    axios
      .post("/fetch-metadata", { url })
      .then(function (response) {
        const { ogTitle, ogDescription, ogImage } = response.data;
        document.getElementById("ogTitle").value = ogTitle || "";
        document.getElementById("ogDescription").value = ogDescription || "";
        document.getElementById("ogImage").value = ogImage || "";
        document.getElementById("metadataForm").style.display = "block";
      })
      .catch(function (error) {
        console.error("Error fetching metadata:", error);
        document.getElementById("metadataForm").style.display = "block";
        showAlert(
          "Metadata could not be fetched. You can still shorten the URL.",
          "success"
        );
      });
  });

document
  .getElementById("metadataForm")
  .addEventListener("submit", function (e) {
    e.preventDefault();
    const url = document.getElementById("urlInput").value;
    const ogTitle = document.getElementById("ogTitle").value;
    const ogDescription = document.getElementById("ogDescription").value;
    const ogImage = document.getElementById("ogImage").value;

    axios
      .post("/shorten", { url, ogTitle, ogDescription, ogImage })
      .then(function (response) {
        showAlert("URL shortened: " + response.data.shortId, "success");
        location.reload();
      })
      .catch(function (error) {
        console.error("Error shortening URL:", error);
        showAlert("Error shortening URL", "error");
      });
  });

function copyLink(shortId) {
  const link = location.href + shortId;
  const el = document.createElement("textarea");
  el.value = link;
  document.body.appendChild(el);
  el.select();
  document.execCommand("copy");
  document.body.removeChild(el);
  showAlert("Shorten link copied to clipboard", "success");
}

function deleteLink(shortId) {
  axios
    .delete(`/delete/${shortId}`)
    .then(function (response) {
      if (response.data.message) {
        const linkRow = document.getElementById(`link-${shortId}`);
        if (linkRow) {
          linkRow.parentNode.removeChild(linkRow);
        }
        showAlert("URL deleted successfully", "success");
      } else {
        showAlert("Error deleting URL: " + response.data.error, "error");
      }
    })
    .catch(function (error) {
      console.error("Error deleting URL:", error);
      showAlert("Error deleting URL: " + error.response.data.error, "error");
    });
}
