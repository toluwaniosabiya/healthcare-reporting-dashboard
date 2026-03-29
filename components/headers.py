import streamlit as st


def render_section_header(title: str, color: str = "#037067") -> None:
    st.markdown(
        f"""
        <div style="margin-top: 1.5rem; margin-bottom: 0.75rem;">
            <div style="
                font-size: 3rem;
                font-weight: 700;
                color: {color};
                line-height: 1.2;
            ">
                {title}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_title_header(title: str, color: str = "#003633") -> None:
    st.markdown(
        f"""
        <div style="margin-top: 1.5rem; margin-bottom: 0.75rem;">
            <div style="
                font-size: 4rem;
                font-weight: 700;
                color: {color};
                line-height: 1.2;
            ">
                {title}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
