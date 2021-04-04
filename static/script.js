var fileUploader1 = document.getElementById("fileUploader1");
var fileUploader2 = document.getElementById("fileUploader2");
fileUploader.addEventListener("change", handleFileUpload, false);

function handleFileUpload(event) {
  var file = event.target.files[0];
  var reader = new FileReader();

  reader.onload = function (e) {
    localStorage.setItem("content", e.target.result);
  };

  reader.readAsText(file, "base64");
}
