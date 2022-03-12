document.addEventListener("DOMContentLoaded", () => {

const uniqueId = (length=16) => {
  return parseInt(Math.ceil(Math.random() * Date.now()).toPrecision(length).toString().replace(".", ""))
}

// ----------------------------

document.querySelector("#create").onclick = () => {
    document.getElementById("meeting_id").disabled = false;


}


document.querySelector("#butt01").onclick = () => {
  document.getElementById("meeting_id").value  = uniqueId()
    document.getElementById("meeting_id").disabled = true;
    document.getElementById("meeting_name").value  = ""
}

ids = []
count = 0
document.querySelector("#butt02").onclick = () => {
  for (let i = 0; i< 1000; i++){
    ids.push(uniqueId())
  }
  for (el of ids){
    for (ell of ids){
      if(el == ell && ids.indexOf(el) != ids.indexOf(ell)){
        count += 1
      }
    }
  }
  document.querySelector("#span02").innerHTML = `Found ${count} duplicated random values.`
};




})