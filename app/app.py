import streamlit as st
import pandas as pd
import numpy as np

from myfunc import (
    prepare_recommendation_system,
    myIBCF,
    get_recommended_movies,
    get_displayed_movies
)

# Load and prepare data
ratings, movies, S_top30, top_10_popular = prepare_recommendation_system()

# Page configuration
st.set_page_config(page_title="Movie Recommender App", layout="wide")

# Initialize session state for storing user ratings
if "user_ratings" not in st.session_state:
    st.session_state.user_ratings = {}

# Sidebar for navigation
st.sidebar.title("Movie Recommender App")
page = st.sidebar.radio("Go to", ["System I - Popularity", "System II - Collaborative"])

def get_movie_card(movie, with_rating=False):
    """
    Create a movie card-like UI block using Streamlit components.
    """
    poster_url = movie['PosterURL'] if pd.notna(movie['PosterURL']) else "https://via.placeholder.com/300x450?text=No+Image"
    title = movie['Title']
    movie_id = movie['movieID']
    
    # Display in a container
    
    st.image(poster_url, use_container_width=True)
    st.markdown(f"**{title}**", unsafe_allow_html=True)
    
    if with_rating:
        # Define star options as in original
        star_options = ["★☆☆☆☆", "★★☆☆☆", "★★★☆☆", "★★★★☆", "★★★★★"]
        rating_key = f"rating_{movie_id}"
        current_value = st.session_state.user_ratings.get(movie_id, None)
        chosen_rating = st.radio(
            "Rate this movie:",
            options=[None, 1, 2, 3, 4, 5],
            format_func=lambda x: star_options[x-1] if x else "No rating",
            index=(current_value if current_value else 0),
            key=rating_key
        )
        # Update session state
        if chosen_rating is not None:
            st.session_state.user_ratings[movie_id] = chosen_rating
    else:
        # No rating input, just show title and poster
        pass


def display_recommendations_with_posters(recommended_df):
    """
    Display recommended movies in a grid using columns.
    """
    # We can try 5 columns as in the original layout
    cols = st.columns(5)
    for i, (_, movie) in enumerate(recommended_df.iterrows()):
        with cols[i % 5]:
            poster_url = movie['PosterURL'] if pd.notna(movie['PosterURL']) else "https://via.placeholder.com/300x450?text=No+Image"
            st.image(poster_url, use_column_width='auto')
            st.markdown(f"**{movie['Title']}**", unsafe_allow_html=True)
            if 'PredictedRating' in movie and not pd.isna(movie['PredictedRating']):
                st.write(f"Predicted Rating: {movie['PredictedRating']:.2f}")
            else:
                st.write("Predicted Rating: N/A")


if page == "System I - Popularity":
    # System I: Show top 10 popular
    st.title("Top 10 Popular Movies")
    st.write("---")
    popular_movies = top_10_popular.head(10)

    # Display in a grid of 5 columns
    cols = st.columns(5)
    for i, (_, movie) in enumerate(popular_movies.iterrows()):
        with cols[i % 5]:
            get_movie_card(movie, with_rating=False)

elif page == "System II - Collaborative":
    # System II: Show 100 sample movies to rate
    st.title("Rate Movies to Get Recommendations")
    st.write("---")

    sample_movies = get_displayed_movies(movies_df=movies, n=100)
    if sample_movies.empty:
        st.write("No movies available to display.")
    else:
        # Display these movies in a similar grid layout
        cols = st.columns(5)
        for i, (_, movie) in enumerate(sample_movies.iterrows()):
            with cols[i % 5]:
                get_movie_card(movie, with_rating=True)

        st.write("---")
        recommend_button = st.button("Get Recommendations", type='primary')
        
        if recommend_button:
            # Collect user ratings
            rating_input = {
                'm' + str(mid): val 
                for mid, val in st.session_state.user_ratings.items() if val is not None
            }

            if not rating_input:
                # No ratings given, show top 10 popular as fallback
                st.info("No ratings provided. Showing top 10 popular movies.")
                recommended_movie_ids = top_10_popular['PrefixedMovieID'].tolist()[:10]
                recommended_df = get_recommended_movies(recommended_movie_ids, movies_df=movies)
                display_recommendations_with_posters(recommended_df)
            else:
                # Construct user ratings series
                user_ratings = pd.Series(data=np.nan, index=['m' + str(mid) for mid in movies['movieID']])
                for movie_id, rating_val in rating_input.items():
                    user_ratings[movie_id] = rating_val

                # Get recommendations
                recommended_movie_ids = myIBCF(
                    newuser=user_ratings,
                    S_top30_df=S_top30,
                    popularity_ranking_df=top_10_popular,
                    n_recommend=10
                )

                recommended_df = get_recommended_movies(recommended_movie_ids, movies_df=movies)
                st.header("Your Recommendations")
                display_recommendations_with_posters(recommended_df)
else:
    # Fallback
    st.title("404: Not Found")
    st.write("The page you selected was not recognized.")
