from analyze import analyze
from ad_hoc import AdHoc

AdHoc.log.observer.addObserver(analyze)
AdHoc(3, 4).logMessage()
