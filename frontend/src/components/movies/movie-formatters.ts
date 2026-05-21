import type { CatalogMovie } from "@/types/catalog";

export function formatMovieDuration(durationMinutes: number) {
  if (!Number.isFinite(durationMinutes) || durationMinutes <= 0) {
    return "Duração indisponível";
  }

  const hours = Math.floor(durationMinutes / 60);
  const minutes = durationMinutes % 60;

  if (hours === 0) {
    return `${minutes}min`;
  }

  if (minutes === 0) {
    return `${hours}h`;
  }

  return `${hours}h ${minutes}min`;
}

export function formatMovieGenres(genres: CatalogMovie["genres"]) {
  if (genres.length === 0) {
    return "Gênero indisponível";
  }

  return genres.map((genre) => genre.name).join(", ");
}

export function getMovieDetailsHref(movieId: CatalogMovie["id"]) {
  return `/movies/${movieId}`;
}
