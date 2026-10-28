from datetime import date
from calendar import monthrange
STAGES=[(3,"奶猫期"),(12,"幼猫期"),(84,"青年成猫"),(120,"中年成猫"),(10000,"老年猫")]
def add_months(day,months):
    year=day.year+(day.month-1+months)//12;month=(day.month-1+months)%12+1
    return date(year,month,min(day.day,monthrange(year,month)[1]))
def age_info(birth,today=None,override=None):
    today=today or date.today();birth=date.fromisoformat(str(birth))
    if birth>today:raise ValueError("出生日期不能晚于今天")
    months=(today.year-birth.year)*12+today.month-birth.month
    if add_months(birth,months)>today:months-=1
    days=(today-add_months(birth,months)).days
    effective=months if override is None else max(0,int(override))
    threshold,stage=next((limit,name) for limit,name in STAGES if effective<limit)
    years=months//12
    human=round(15*min(months/12,1)+9*max(0,min(months/12-1,1))+4*max(0,months/12-2))
    next_day=add_months(birth,threshold) if threshold<10000 else None
    return {"years":years,"months":months%12,"days":days,"total_months":months,"total_days":(today-birth).days,
            "effective_months":effective,"stage":stage,"human_years":human,
            "next_days":max(0,(next_day-today).days) if next_day else None,"text":f"{years}岁{months%12}个月{days}天"}
