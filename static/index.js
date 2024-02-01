document
  .getElementById("fetchMetadataButton")
  .addEventListener("click", function () {
    const url = document.getElementById("urlInput").value;
    if (!url) {
      alert("Please enter a URL.");
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
        alert("Metadata could not be fetched. You can still shorten the URL.");
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
        alert("URL shortened: " + response.data.shortId);
        location.reload();
      })
      .catch(function (error) {
        console.error("Error shortening URL:", error);
        alert("Error shortening URL");
      });
  });

function deleteLink(shortId) {
  axios
    .delete(`/delete/${shortId}`)
    .then(function (response) {
      if (response.data.message) {
        const linkRow = document.getElementById(`link-${shortId}`);
        if (linkRow) {
          linkRow.parentNode.removeChild(linkRow);
        }
        alert("URL deleted successfully");
      } else {
        alert("Error deleting URL: " + response.data.error);
      }
    })
    .catch(function (error) {
      console.error("Error deleting URL:", error);
      alert("Error deleting URL: " + error.response.data.error);
    });
}
