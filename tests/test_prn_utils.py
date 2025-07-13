import pytest
import core_framework.prn_utils as prn


def test_get_prn_scope():
    assert prn.get_prn_scope("prn") == prn.SCOPE_CLIENT
    assert prn.get_prn_scope("prn:portfolio") == prn.SCOPE_PORTFOLIO
    assert prn.get_prn_scope("prn:portfolio:app") == prn.SCOPE_APP
    assert prn.get_prn_scope("prn:portfolio:app:branch") == prn.SCOPE_BRANCH
    assert prn.get_prn_scope("prn:portfolio:app:branch:build") == prn.SCOPE_BUILD
    assert (
        prn.get_prn_scope("prn:portfolio:app:branch:build:component")
        == prn.SCOPE_COMPONENT
    )
    assert prn.get_prn_scope("prn:portfolio:app:branch:build:component:extra") is None


def test_extract_prn():
    prn_str = "prn:portfolio:app:branch:build:component"
    assert prn.extract_prn(prn_str) == prn_str
    assert prn.extract_prn({"prn": prn_str}) == prn_str

    class Obj:
        prn = prn_str

    assert prn.extract_prn(Obj()) == prn_str


def test_extract_portfolio():
    prn_str = "prn:portfolio:app:branch:build:component"
    assert prn.extract_portfolio(prn_str) == "portfolio"
    assert prn.extract_portfolio({"prn": prn_str}) == "portfolio"


def test_extract_app():
    prn_str = "prn:portfolio:app:branch:build:component"
    assert prn.extract_app(prn_str) == "app"
    assert prn.extract_app({"prn": prn_str}) == "app"


def test_extract_branch():
    prn_str = "prn:portfolio:app:branch:build:component"
    assert prn.extract_branch(prn_str) == "branch"
    assert prn.extract_branch({"prn": prn_str}) == "branch"


def test_extract_build():
    prn_str = "prn:portfolio:app:branch:build:component"
    assert prn.extract_build(prn_str) == "build"
    assert prn.extract_build({"prn": prn_str}) == "build"


def test_extract_component():
    prn_str = "prn:portfolio:app:branch:build:component"
    assert prn.extract_component(prn_str) == "component"
    assert prn.extract_component({"prn": prn_str}) == "component"


def test_extract_portfolio_prn():
    prn_str = "prn:portfolio"
    assert prn.extract_portfolio_prn(prn_str) == prn_str
    assert prn.extract_portfolio_prn("invalid") == prn.V_EMPTY


def test_extract_app_prn():
    prn_str = "prn:portfolio:app"
    assert prn.extract_app_prn(prn_str) == prn_str
    assert prn.extract_app_prn("invalid") == prn.V_EMPTY


def test_extract_branch_prn():
    prn_str = "prn:portfolio:app:branch"
    assert prn.extract_branch_prn(prn_str) == prn_str
    assert prn.extract_branch_prn("invalid") == prn.V_EMPTY


def test_extract_build_prn():
    prn_str = "prn:portfolio:app:branch:build"
    assert prn.extract_build_prn(prn_str) == prn_str
    assert prn.extract_build_prn("invalid") == prn.V_EMPTY


def test_extract_component_prn():
    prn_str = "prn:portfolio:app:branch:build:component"
    assert prn.extract_component_prn(prn_str) == prn_str
    assert prn.extract_component_prn("invalid") == prn.V_EMPTY


def test_generate_prn():
    request = {
        "prn": "prn:portfolio:app:branch:build:component",
        "portfolio_prn": "prn:portfolio",
        "app_prn": "prn:portfolio:app",
        "branch_prn": "prn:portfolio:app:branch",
        "build_prn": "prn:portfolio:app:branch:build",
        "component_prn": "prn:portfolio:app:branch:build:component",
        "name": "component",
    }
    assert prn.generate_prn(prn.SCOPE_PORTFOLIO, request) == "prn:portfolio"
    assert prn.generate_prn(prn.SCOPE_APP, request) == "prn:portfolio:app"
    assert prn.generate_prn(prn.SCOPE_BRANCH, request) == "prn:portfolio:app:branch"
    assert (
        prn.generate_prn(prn.SCOPE_BUILD, request) == "prn:portfolio:app:branch:build"
    )
    assert (
        prn.generate_prn(prn.SCOPE_COMPONENT, request)
        == "prn:portfolio:app:branch:build:component"
    )
    assert prn.generate_prn("invalid", request) is None


def test_validate_prn():
    prn_str = "prn:portfolio:app:branch:build:component"
    assert prn.validate_prn(prn.SCOPE_PORTFOLIO, "prn:portfolio") is True
    assert prn.validate_prn(prn.SCOPE_APP, "prn:portfolio:app") is True
    assert prn.validate_prn(prn.SCOPE_BRANCH, "prn:portfolio:app:branch") is True
    assert prn.validate_prn(prn.SCOPE_BUILD, "prn:portfolio:app:branch:build") is True
    assert prn.validate_prn(prn.SCOPE_COMPONENT, prn_str) is True
    assert prn.validate_prn("invalid", prn_str) is False


def test_validate_item_type():
    assert prn.validate_item_type(prn.SCOPE_PORTFOLIO) is True
    assert prn.validate_item_type("invalid") is False


def test_generate_portfolio_prn():
    request = {"build_prn": "prn:portfolio:app:branch:build"}
    assert prn.generate_portfolio_prn(request) == "prn:portfolio"
    request = {"branch_prn": "prn:portfolio:app:branch"}
    assert prn.generate_portfolio_prn(request) == "prn:portfolio"
    request = {"app_prn": "prn:portfolio:app"}
    assert prn.generate_portfolio_prn(request) == "prn:portfolio"
    request = {"prn": "prn:portfolio"}
    assert prn.generate_portfolio_prn(request) == "prn:portfolio"
    request = {"portfolio_prn": "prn:portfolio"}
    assert prn.generate_portfolio_prn(request) == "prn:portfolio"
    request = {"name": "portfolio"}
    assert prn.generate_portfolio_prn(request) == "prn:portfolio"


def test_generate_app_prn():
    request = {"build_prn": "prn:portfolio:app:branch:build"}
    assert prn.generate_app_prn(request) == "prn:portfolio:app"
    request = {"branch_prn": "prn:portfolio:app:branch"}
    assert prn.generate_app_prn(request) == "prn:portfolio:app"
    request = {"prn": "prn:portfolio:app"}
    assert prn.generate_app_prn(request) == "prn:portfolio:app"
    request = {"app_prn": "prn:portfolio:app"}
    assert prn.generate_app_prn(request) == "prn:portfolio:app"
    request = {"portfolio_prn": "prn:portfolio", "name": "app"}
    assert prn.generate_app_prn(request) == "prn:portfolio:app"


def test_branch_short_name():
    name = "Feature/Some-Branch-Name_123"
    short = prn.branch_short_name(name)
    assert isinstance(short, str)
    assert len(short) <= 20


def test_generate_branch_prn():
    request = {"build_prn": "prn:portfolio:app:branch:build"}
    assert prn.generate_branch_prn(request) == "prn:portfolio:app:branch"
    request = {"prn": "prn:portfolio:app:branch"}
    assert prn.generate_branch_prn(request) == "prn:portfolio:app:branch"
    request = {"branch_prn": "prn:portfolio:app:branch"}
    assert prn.generate_branch_prn(request) == "prn:portfolio:app:branch"
    request = {"app_prn": "prn:portfolio:app", "name": "branch"}
    assert prn.generate_branch_prn(request).startswith("prn:portfolio:app:")


def test_generate_build_prn():
    request = {"prn": "prn:portfolio:app:branch:build"}
    assert prn.generate_build_prn(request) == "prn:portfolio:app:branch:build"
    request = {"build_prn": "prn:portfolio:app:branch:build"}
    assert prn.generate_build_prn(request) == "prn:portfolio:app:branch:build"
    request = {"branch_prn": "prn:portfolio:app:branch", "name": "build"}
    assert prn.generate_build_prn(request).startswith("prn:portfolio:app:branch:")


def test_generate_component_prn():
    request = {"prn": "prn:portfolio:app:branch:build:component"}
    assert (
        prn.generate_component_prn(request)
        == "prn:portfolio:app:branch:build:component"
    )
    request = {"component_prn": "prn:portfolio:app:branch:build:component"}
    assert (
        prn.generate_component_prn(request)
        == "prn:portfolio:app:branch:build:component"
    )
    request = {"build_prn": "prn:portfolio:app:branch:build", "name": "component"}
    assert prn.generate_component_prn(request).startswith(
        "prn:portfolio:app:branch:build:"
    )


def test_validate_item_prn():
    assert prn.validate_item_prn("prn:portfolio:app:branch:build:component") is True
    assert prn.validate_item_prn("invalid") is False


def test_validate_portfolio_prn():
    assert prn.validate_portfolio_prn("prn:portfolio") is True
    assert prn.validate_portfolio_prn("invalid") is False


def test_validate_app_prn():
    assert prn.validate_app_prn("prn:portfolio:app") is True
    assert prn.validate_app_prn("invalid") is False


def test_validate_branch_prn():
    assert prn.validate_branch_prn("prn:portfolio:app:branch") is True
    assert prn.validate_branch_prn("invalid") is False


def test_validate_build_prn():
    assert prn.validate_build_prn("prn:portfolio:app:branch:build") is True
    assert prn.validate_build_prn("invalid") is False


def test_validate_component_prn():
    assert (
        prn.validate_component_prn("prn:portfolio:app:branch:build:component") is True
    )
    assert prn.validate_component_prn("invalid") is False


def test_get_prn_scope_valid():
    assert prn.get_prn_scope("prn") == prn.SCOPE_CLIENT
    assert prn.get_prn_scope("prn:portfolio") == prn.SCOPE_PORTFOLIO
    assert prn.get_prn_scope("prn:portfolio:app") == prn.SCOPE_APP
    assert prn.get_prn_scope("prn:portfolio:app:branch") == prn.SCOPE_BRANCH
    assert prn.get_prn_scope("prn:portfolio:app:branch:build") == prn.SCOPE_BUILD
    assert (
        prn.get_prn_scope("prn:portfolio:app:branch:build:component")
        == prn.SCOPE_COMPONENT
    )


def test_get_prn_scope_invalid():
    # More than 5 colons
    assert prn.get_prn_scope("prn:portfolio:app:branch:build:component:extra") is None
    # Empty string
    assert prn.get_prn_scope("") == prn.SCOPE_CLIENT
    # Only colons
    assert prn.get_prn_scope(":") == prn.SCOPE_PORTFOLIO
    assert prn.get_prn_scope("::") == prn.SCOPE_APP
    assert prn.get_prn_scope(":::") == prn.SCOPE_BRANCH
    assert prn.get_prn_scope("::::") == prn.SCOPE_BUILD
    assert prn.get_prn_scope(":::::") == prn.SCOPE_COMPONENT
    assert prn.get_prn_scope("::::::") is None
    # Missing prn prefix.  It's not really a 'prn' prefix.  It's the 'client'.  So, the following is 2 colons, or SCOPE_APP
    assert prn.get_prn_scope("portfolio:app:branch") == prn.SCOPE_APP
