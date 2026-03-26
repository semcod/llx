import yaml
import sys
sys.path.insert(0, '/home/tom/github/semcod/llx')

def test():
    from llx.planfile.generate_strategy import _normalize_strategy_data
    
    focus = "complexity"
    data = {
        'name': 'Refactoring Strategy',
        'project_type': 'python',
        'domain': 'software',
        'goal': focus or 'improvement',
        'sprints': [{
            'id': 1, 'name': 'Sprint 1', 'objectives': ['Reduce complexity', 'Add tests'],
            'tasks': [
                {'name': 'Analyze Complexity', 'description': 'Analyze code complexity', 'type': 'feature', 'model_hints': 'balanced'},
                {'name': 'Add Tests', 'description': 'Add unit tests', 'type': 'test', 'model_hints': 'cheap'}
            ]
        }],
        'quality_gates': ['Average CC < 5', 'Test coverage >= 80%']
    }

    data = _normalize_strategy_data(data)
    
    if 'name' not in data:
        data['name'] = f"Refactoring Strategy"
    if 'project_type' not in data:
        data['project_type'] = 'python'
    if 'domain' not in data:
        data['domain'] = 'software'
    
    if 'goal' not in data or isinstance(data.get('goal'), str):
        goal_str = data.get('goal', focus or 'improvement')
        data['goal'] = {
            'short': f"Improve {goal_str}" if goal_str else "Improve codebase",
            'quality': ['Reduce complexity', 'Improve maintainability'],
            'delivery': ['Complete in sprints', 'Review changes'],
            'metrics': ['Complexity reduction', 'Test coverage']
        }
    elif isinstance(data.get('goal'), dict):
        goal = data['goal']
        goal.setdefault('short', f"Improve {focus or 'codebase'}")
        goal.setdefault('quality', ['Reduce complexity', 'Improve maintainability'])
        goal.setdefault('delivery', ['Complete in sprints', 'Review changes'])
        goal.setdefault('metrics', ['Complexity reduction', 'Test coverage'])
        
test()
print("Test completed successfully without 'get' error.")
