document.getElementById("submitPasscodeButton").addEventListener("click", function () {
    const passcode = document.getElementById("passcodeInput").value;

    console.log("Validating passcode:", passcode);

    axios
      .post("/validate-passcode", { passcode })
      .then(function (response) {
        location.reload();
      })
      .catch(function (error) {
        console.error("Error validating passcode:", error);
        alert("Incorrect passcode. Please try again.");
      });
});
