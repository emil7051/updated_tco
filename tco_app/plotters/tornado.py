import plotly.graph_objects as go


def create_tornado_chart(base_tco, sensitivity_results):
    """Create a tornado chart illustrating the impact of parameters on TCO."""
    parameters, lower_impacts, upper_impacts = [], [], []
    for param, impacts in sorted(
        sensitivity_results.items(),
        key=lambda x: max(abs(x[1]["min_impact"]), abs(x[1]["max_impact"])),
        reverse=True,
    ):
        parameters.append(param)
        lower_impacts.append(impacts["min_impact"])
        upper_impacts.append(impacts["max_impact"])

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=parameters,
            x=lower_impacts,
            orientation="h",
            name="Lower Value Impact",
            marker=dict(color="blue"),
            base=base_tco,
            hoverinfo="text",
            hovertext=[
                f"{p}: {i:.4f} AUD/km" for p, i in zip(parameters, lower_impacts)
            ],
        )
    )
    fig.add_trace(
        go.Bar(
            y=parameters,
            x=upper_impacts,
            orientation="h",
            name="Upper Value Impact",
            marker=dict(color="red"),
            base=base_tco,
            hoverinfo="text",
            hovertext=[
                f"{p}: {i:.4f} AUD/km" for p, i in zip(parameters, upper_impacts)
            ],
        )
    )

    fig.update_layout(
        title="Tornado Chart: Impact of Parameters on BEV TCO",
        xaxis_title="TCO per km (AUD)",
        yaxis=dict(title="Parameter", categoryorder="array", categoryarray=parameters),
        barmode="overlay",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        height=400,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    fig.add_vline(
        x=base_tco,
        line_width=2,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Base TCO: {base_tco:.4f}",
        annotation_position="top right",
    )
    return fig
