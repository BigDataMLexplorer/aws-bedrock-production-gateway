from app.costs import Pricing, estimate_cost
from app.models import Usage


def test_cost_estimate():
    c=estimate_cost(Usage(input_tokens=1_000_000,output_tokens=500_000,total_tokens=1_500_000),Pricing(2.0,6.0))
    assert c==5.0
