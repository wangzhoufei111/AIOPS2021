# zhuque_platform

zhuque_platform is anomaly detection platform . It is built with [Python][0] using the [Django Web Framework][1].

## Installation

### Quick start

Install all dependencies:

    pip install -r requirements.txt

Run migrations:
    
    python manage.py makemigrations
    python manage.py migrate

运行脚本:
    
    1.到根路径执行python manage.py shell, 然后python语法执行scripts下的的脚本
    2.python manage.py runserver 0.0.0.0:8080 后台进入 账号密码admin admin123查看数据库表数据


时间序列参数训练:
Rule表共有1909条告警规则
    1.generate_kpi_rule.py 生成kpi的告警规则
    2.generate_performance_rule.py 生成性能指标的告警规则
StatisticMetric表共有1909条时序统计量
    1.generate_kpi_statistic.py 根据GeneratorStandardNsigma计算kpi指标的N和sigma
    2.generate_performance_statistic.py 根据GeneratorStandardNsigma计算性能指标的N和sigma

风险事件检测模块:

    1.参考test_risk_module.py案例，输入是一段时间窗口内的ts、instance、instance_type，输入是这段窗口内的风险事件，其中异常事件检测模型需要加载Rule和StatisticMetric表中的一些统计量

后续安排:

    1.日志模板训练，同样生成时序metric，按照上述逻辑存储在Rule和StatisticMetric表中，难点是日志的清洗，以及是否需要人为标记
    2.风险事件模块产生的风险事件保存至RiskEvents