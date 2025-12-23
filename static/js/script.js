async function getBooks() {
  const res = await fetch("http://127.0.0.1:8000/api/books/");
  const data = await res.json();
  console.log(data);
}
