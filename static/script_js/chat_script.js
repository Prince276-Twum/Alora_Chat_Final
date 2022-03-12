document.addEventListener("DOMContentLoaded", () => {
    var socket = io();
    const BOT_IMG = "https://image.flaticon.com/icons/svg/327/327779.svg";
    const PERSON_IMG = "https://image.flaticon.com/icons/svg/145/145867.svg";

    const msgerForm = get(".msger-inputarea");
    const msgerInput = get(".msger-input");
    const msgerChat = get(".msger-chat");

    const real_username = document.querySelector("#user-id-n").innerHTML;
    console.log(real_username)
    EnterRoom("man");

    msgerForm.addEventListener("submit", event => {
    event.preventDefault();
    socket.emit("incoming", {"msg":document.querySelector("#msg_input").value, "room":"man", "username":real_username})
    msgerInput.value = "";
 });


    socket.on("message", data => {
        if (data.msg) {

        if (data.username == real_username) {
                appendMessage(real_username, PERSON_IMG, "right", data.msg)

         }
         else {
            appendMessage(data.username, PERSON_IMG, "left", data.msg)
         }
}

})
//displaying message
function appendMessage(name, img, side, text) {
  const msgHTML = `
    <div class="msg ${side}-msg">
      <div class="msg-img" style="background-image: url(${img})"></div>

      <div class="msg-bubble">
        <div class="msg-info">
          <div class="msg-info-name">${name}</div>
          <div class="msg-info-time">${formatDate(new Date())}</div>
        </div>

        <div class="msg-text">${text}</div>
      </div>
    </div>
  `;

  msgerChat.insertAdjacentHTML("beforeend", msgHTML);
  msgerChat.scrollTop += 500;
}

// Utils
function get(selector, root = document) {
  return root.querySelector(selector);
}

function formatDate(date) {
  const h = "0" + date.getHours();
  const m = "0" + date.getMinutes();

  return `${h.slice(-2)}:${m.slice(-2)}`;
}

function random(min, max) {
  return Math.floor(Math.random() * (max - min) + min);
}


    function EnterRoom(room) {
        socket.emit("join", {"room": "man", "username": real_username})
    }


})

