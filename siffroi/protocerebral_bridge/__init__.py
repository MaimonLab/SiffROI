try:
    from .protocols.fit_von_mises import FitVonMises
except ImportError:
    # FourCorr is not installed
    print("FourCorr is not installed, so the FitVonMises protocol is not available.")