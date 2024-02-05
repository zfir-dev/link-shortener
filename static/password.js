document
    .getElementById("submitPasscodeButton")
    .addEventListener("click", function () {
        const passcode = document.getElementById("passcodeInput").value;
        axios
            .post("/validate-passcode", {passcode})
            .then(function (response) {
                location.reload();
            })
            .catch(function (error) {
                console.error("Error validating passcode:", error);
                showAlert("Incorrect passcode. Please try again.", "error");
            });
    });
