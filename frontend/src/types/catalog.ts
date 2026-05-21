export type MovieStatus = "em_cartaz" | "pre_venda";

export type CatalogGenre = {
  id: string;
  name: string;
};

export type CatalogMovie = {
  id: string;
  title: string;
  genres: CatalogGenre[];
  duration_minutes: number;
  poster_url: string;
  status: MovieStatus;
  is_featured: boolean;
};
