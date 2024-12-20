import streamlit as st
import pandas as pd
import numpy as np

from myfunc import (
    prepare_recommendation_system,
    myIBCF,
    get_recommended_movies,
    get_displayed_movies
)

# Page configuration
st.set_page_config(page_title="Movie Recommender App", layout="wide")

# Cache data loading to improve performance
@st.cache_data
def load_data():
    return prepare_recommendation_system()

ratings, movies, S_top30, top_10_popular = load_data()

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
    
    # # Display poster and title
    # st.image(poster_url, use_container_width=True)#st.image(poster_url, width=250)
    # st.markdown(f"**{title}**", unsafe_allow_html=True)
     # Custom card layout using Streamlit's markdown and container
    card_style = """
        <style>
        .movie-card {
            background-color: #424952;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            height: 400px;
            width: 220px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            margin: auto;
        }
        .movie-card img {
            max-height: 300px;
            object-fit: cover;
            margin-bottom: 5px;
        }
        .movie-card h6 {
            font-size: 16px;
            margin: 0;
            flex-grow: 1;
        }
        </style>
    """

    # Card content with optional rating
    card_content = f"""
        <div class="movie-card">
            <img src="{poster_url}" alt="{title}">
            <h6>{title}</h6>
        </div>
    """

    # Render the card
    st.markdown(card_style, unsafe_allow_html=True)
    st.markdown(card_content, unsafe_allow_html=True)
    
    if with_rating:
        # Define star options as in original
        star_options = ["★☆☆☆☆", "★★☆☆☆", "★★★☆☆", "★★★★☆", "★★★★★"]
        rating_key = f"rating_{movie_id}"
        current_value = st.session_state.user_ratings.get(movie_id, None)
        
        radio_index = current_value if current_value else 0
        
        chosen_rating = st.radio(
            "Rate this movie:",
            options=[None, 1, 2, 3, 4, 5],
            format_func=lambda x: star_options[x-1] if x else "No rating",
            index=radio_index,
            key=rating_key
        )
        
        # Update session state if a rating is chosen
        if chosen_rating is not None:
            st.session_state.user_ratings[movie_id] = chosen_rating
        else:
            # If user selects "No rating", remove it from user_ratings if it exists
            if movie_id in st.session_state.user_ratings:
                del st.session_state.user_ratings[movie_id]


def display_recommendations_with_posters(recommended_df):
    """
    Display recommended movies in a grid using columns, styled similarly to get_movie_card.
    """
    # Custom CSS for the movie cards
    card_style = """
        <style>
        .movie-card {
            background-color: #ABCDEF;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            height: 400px;
            width: 220px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            margin: auto;
        }
        .movie-card img {
            max-height: 300px;
            object-fit: cover;
            margin-bottom: 5px;
            border-radius: 4px;
        }
        .movie-card h6 {
            font-size: 16px;
            margin: 0;
            flex-grow: 1;
        }
        </style>
    """
    # Inject the CSS into Streamlit
    st.markdown(card_style, unsafe_allow_html=True)

    # Create a grid of columns to display the cards
    cols = st.columns(5)  # Adjust the number of columns as needed
    for i, (_, movie) in enumerate(recommended_df.iterrows()):
        with cols[i % 5]:
            # Movie card content
            poster_url = movie['PosterURL'] if pd.notna(movie['PosterURL']) else "https://via.placeholder.com/300x450?text=No+Image"
            card_content = f"""
                <div class="movie-card">
                    <img src="{poster_url}" alt="{movie['Title']}">
                    <h6>{movie['Title']}</h6>
                </div>
            """
            st.markdown(card_content, unsafe_allow_html=True)



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
    
    if "sample_movies" not in st.session_state:
        st.session_state.sample_movies = get_displayed_movies(movies_df=movies, n=100)
        print("Selected 100 movies: 70 popular and 30 random.")  # This will print only once

    sample_movies = st.session_state.sample_movies
    # sample_movies = get_displayed_movies(movies_df=movies, n=100)
    if sample_movies.empty:
        st.write("No movies available to display.")
    else:
        # Display these movies in a similar grid layout
        cols = st.columns(5)
        for i, (_, movie) in enumerate(sample_movies.iterrows()):
            with cols[i % 5]:
                get_movie_card(movie, with_rating=True)

        st.write("---")
        # Recommendation button
        recommend_button = st.button("Get Recommendations")

        if recommend_button:
            # Collect user ratings
            rating_input = {
                'm' + str(mid): val 
                for mid, val in st.session_state.user_ratings.items() if val is not None
            }

            if not rating_input:
                # No ratings given, show top 10 popular as default
                st.info("No ratings provided. Showing top 10 popular movies.")
                recommended_movie_ids = top_10_popular['PrefixedMovieID'].tolist()[:10]
                recommended_df = get_recommended_movies(recommended_movie_ids, movies_df=movies)
                st.header("Your Recommendations")
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
