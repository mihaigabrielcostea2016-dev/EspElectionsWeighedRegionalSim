import streamlit as st

st.set_page_config(page_title="Spanish Congress Simulator", layout="wide")

# 52 Constituencies seat distribution (350 total seats)
CONSTITUENCIES_SEATS = {
    "Madrid": 37, "Barcelona": 32, "Valencia": 16, "Alicante": 12, "Sevilla": 12,
    "Málaga": 11, "Murcia": 10, "Cádiz": 9, "Biscay (Bizkaia)": 8, "A Coruña": 8,
    "Balearic Islands": 8, "Las Palmas": 8, "Asturias": 7, "Santa Cruz de Tenerife": 7,
    "Zaragoza": 7, "Pontevedra": 7, "Granada": 7, "Tarragona": 6, "Córdoba": 6,
    "Girona": 6, "Gipuzkoa": 6, "Almería": 6, "Toledo": 6, "Badajoz": 6,
    "Jaén": 5, "Navarre": 5, "Castellón": 5, "Cantabria": 5, "Valladolid": 5,
    "Ciudad Real": 5, "Huelva": 5, "León": 4, "Lleida": 4, "Cáceres": 4,
    "Albacete": 4, "Burgos": 4, "Lugo": 4, "Ourense": 4, "Salamanca": 4,
    "Álava": 4, "La Rioja": 4, "Guadalajara": 4, "Huesca": 3, "Cuenca": 3,
    "Zamora": 3, "Ávila": 3, "Palencia": 3, "Segovia": 3, "Teruel": 3,
    "Soria": 2, "Ceuta": 1, "Melilla": 1
}

# Regional party Scope Definition
# Defines which specific constituencies regional parties are permitted to run in
REGIONAL_PARTY_SCOPES = {
    "ERC": ["Barcelona", "Girona", "Lleida", "Tarragona"],
    "JUNTS": ["Barcelona", "Girona", "Lleida", "Tarragona"],
    "EAJ-PNV": ["Álava", "Biscay (Bizkaia)", "Gipuzkoa"],
    "EH BILDU": ["Álava", "Biscay (Bizkaia)", "Gipuzkoa", "Navarre"]
}

def dhondt_allocation(votes: dict[str, int], total_seats: int, threshold_pct: float = 3.0) -> dict[str, int]:
    """Calculates seat allocation for a single constituency using D'Hondt method."""
    total_valid_votes = sum(votes.values())
    if total_valid_votes == 0:
        return {party: 0 for party in votes}

    # Filter out parties failing the local constituency 3% threshold
    eligible_parties = {
        party: count for party, count in votes.items()
        if (count / total_valid_votes) * 100 >= threshold_pct
    }

    seats = {party: 0 for party in votes}
    if not eligible_parties:
        return seats

    quotients = []
    for party, party_votes in eligible_parties.items():
        for d in range(1, total_seats + 1):
            quotients.append((party_votes / d, party))

    quotients.sort(key=lambda x: x[0], reverse=True)
    for i in range(total_seats):
        winning_party = quotients[i][1]
        seats[winning_party] += 1

    return seats

def simulate_election(national_vote_shares: dict[str, float]) -> dict[str, int]:
    """Simulates the election applying regional scope restrictions to local parties."""
    total_share = sum(national_vote_shares.values())
    if total_share == 0:
        return {p: 0 for p in national_vote_shares}
    
    normalized_shares = {p: v / total_share for p, v in national_vote_shares.items()}
    national_seats = {party: 0 for party in national_vote_shares}

    for region, seats in CONSTITUENCIES_SEATS.items():
        constituency_voters = seats * 50_000 
        region_votes = {}
        
        for party, share in normalized_shares.items():
            # Apply regional restriction check
            if party in REGIONAL_PARTY_SCOPES:
                allowed_regions = REGIONAL_PARTY_SCOPES[party]
                if region in allowed_regions:
                    # In allowed regions, scale up regional vote share to match local presence
                    region_votes[party] = int(constituency_voters * share * 5.0)
                else:
                    # Non-allowed regions get 0 votes
                    region_votes[party] = 0
            else:
                # National parties receive votes everywhere
                region_votes[party] = int(constituency_voters * share)

        region_seats = dhondt_allocation(region_votes, seats, threshold_pct=3.0)
        for party, seat_count in region_seats.items():
            national_seats[party] += seat_count

    return national_seats

# App Header
st.title("🇪🇸 Spanish Congress Electoral Simulator")
st.markdown("Interactive D'Hondt simulator featuring **regional party scoping** (ERC, Junts, Bildu, and PNV restricted strictly to Catalonia, the Basque Country, and Navarre).")

# Sidebar Controls for Editing Vote Shares
st.sidebar.header("National Vote Shares (%)")

default_shares = {
    "PP": 33.1,
    "PSOE": 31.7,
    "VOX": 12.4,
    "SUMAR": 12.3,
    "ERC": 1.9,
    "JUNTS": 1.6,
    "EH BILDU": 1.4,
    "EAJ-PNV": 1.1,
    "OTHERS": 4.5
}

user_shares = {}
for party, default_val in default_shares.items():
    user_shares[party] = st.sidebar.slider(party, 0.0, 50.0, default_val, 0.1)

# Run Simulation
results = simulate_election(user_shares)
sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

# Main Display Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Seat Distribution (Target: 350 Seats)")
    chart_data = {party: seats for party, seats in sorted_results}
    st.bar_chart(chart_data)
    
    # Results Breakdown Table
    st.dataframe(
        [
            {
                "Party": p, 
                "Seats": s, 
                "National Share (%)": user_shares[p],
                "Scope": ", ".join(REGIONAL_PARTY_SCOPES[p]) if p in REGIONAL_PARTY_SCOPES else "Nationwide"
            } 
            for p, s in sorted_results
        ],
        use_container_width=True
    )

with col2:
    st.subheader("Pactómetro (Coalition Builder)")
    st.markdown("Select parties to test a government investiture majority (**176 seats**):")
    
    selected_coalition = []
    for party, _ in sorted_results:
        if st.checkbox(f"{party} ({results[party]} seats)"):
            selected_coalition.append(party)
            
    coalition_total = sum(results.get(p, 0) for p in selected_coalition)
    
    st.metric(label="Coalition Total Seats", value=f"{coalition_total} / 350")
    
    if coalition_total >= 176:
        st.success(f"🎉 **Absolute Majority Reached!** (+{coalition_total - 176} over threshold)")
    else:
        st.markdown(f"🔴 **Short of Majority** (Needs {176 - coalition_total} more seats)")