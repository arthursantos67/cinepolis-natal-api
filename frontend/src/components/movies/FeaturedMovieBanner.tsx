import Link from "next/link";

import type { CatalogMovie } from "@/types/catalog";

import {
  formatMovieDuration,
  formatMovieGenres,
  getMovieDetailsHref,
} from "./movie-formatters";

type FeaturedMovieBannerProps = {
  movie: CatalogMovie;
  primaryActionLabel?: string;
};

export function FeaturedMovieBanner({
  movie,
  primaryActionLabel = "Ver sessões",
}: FeaturedMovieBannerProps) {
  return (
    <section
      aria-label={`Filme em destaque: ${movie.title}`}
      className="featured-movie"
    >
      <div className="featured-movie__media">
        {/* API poster URLs are arbitrary remote images until image domains are configured. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          alt={`Poster de ${movie.title}`}
          className="featured-movie__poster"
          loading="eager"
          src={movie.poster_url}
        />
      </div>
      <div className="featured-movie__content">
        <p className="eyebrow">Destaque</p>
        <h2>{movie.title}</h2>
        <p className="featured-movie__meta">
          {formatMovieGenres(movie.genres)} |{" "}
          {formatMovieDuration(movie.duration_minutes)}
        </p>
        <Link
          aria-label={`${primaryActionLabel} de ${movie.title}`}
          className="button button-primary"
          href={getMovieDetailsHref(movie.id)}
        >
          {primaryActionLabel}
        </Link>
      </div>
    </section>
  );
}
