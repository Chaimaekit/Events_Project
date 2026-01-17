// ---- Section 1: Carousel ----
const carousel = document.getElementById("carousel");

async function loadCarouselEvents() {
  const res = await fetch(`/events?page=1&size=10`);
  const data = await res.json();
  const events = data.events;

  carousel.innerHTML = "";
  events.forEach(event => {
    const card = document.createElement("div");
    card.className = "event-card";
    card.innerHTML = `
      <img src="${event.image || 'https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?q=80&w=870&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D'}" alt="${event.name}">
      <h2>${event.name}</h2>
      <p><strong>Date:</strong> ${event.date?.startAt || "Unknown"}</p>
      <p><strong>Location:</strong> ${event.place || "Unknown"}</p>
      <p>${event.description?.slice(0, 100) || ""}...</p>
      <a href="${event.url}" target="_blank" style="color: var(--accent);">More Info</a>
    `;
    carousel.appendChild(card);
  });
}

loadCarouselEvents();

// ---- Section 2: Event List + Pagination ----
const eventList = document.getElementById("event-list");
const pagination = document.getElementById("pagination");

const pageSize = 10;
let currentPage = 1;
let totalPages = 1;
const pageBlockSize = 7;
let currentBlock = 0;

async function loadEvents(page = 1) {
  const res = await fetch(`/events?page=${page}&size=${pageSize}`);
  const data = await res.json();

  currentPage = data.page;
  totalPages = data.pages;
  currentBlock = Math.floor((currentPage - 1) / pageBlockSize);

  renderEventList(data.events);
  renderPagination();
}

function renderEventList(events) {
  eventList.innerHTML = "";
  events.forEach(event => {
    const div = document.createElement("div");
    div.className = "event-card";
    div.innerHTML = `
      <h3>${event.name}</h3>
      <p><strong>Date:</strong> ${event.date?.startAt || "Unknown"}</p>
      <p><strong>Location:</strong> ${event.place || "Unknown"}</p>
      <p>${event.description?.slice(0, 120) || ""}...</p>
      <a href="${event.url}" target="_blank" style="color: var(--accent);">More Info</a>
    `;
    eventList.appendChild(div);
  });
}

function renderPagination() {
  pagination.innerHTML = "";
  const startPage = currentBlock * pageBlockSize + 1;
  const endPage = Math.min(startPage + pageBlockSize - 1, totalPages);

  if (currentBlock > 0) {
    const prevBlock = document.createElement("button");
    prevBlock.textContent = "<<";
    prevBlock.onclick = () => { currentBlock--; loadEvents(currentBlock * pageBlockSize + 1); };
    pagination.appendChild(prevBlock);
  }

  for (let i = startPage; i <= endPage; i++) {
    const btn = document.createElement("button");
    btn.textContent = i;
    if (i === currentPage) btn.classList.add("active");
    btn.onclick = () => loadEvents(i);
    pagination.appendChild(btn);
  }

  if (endPage < totalPages) {
    const nextBlock = document.createElement("button");
    nextBlock.textContent = ">>";
    nextBlock.onclick = () => { currentBlock++; loadEvents(currentBlock * pageBlockSize + 1); };
    pagination.appendChild(nextBlock);
  }
}

loadEvents(1);
