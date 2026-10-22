"""Check frozen v10 forecasts against legal native wall flights.

This is a physics fixture, not a tournament or a policy-timing measurement.
Only legal formations and ordinary player commands are used; no state or
configuration is injected and neither engine nor physics is modified.
"""
import importlib.util,json,math,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'student-sdk'))
from soccer import PlayerAction,SoccerEnv,TeamAction,TeamController


def main():
    spec=importlib.util.spec_from_file_location('frozen_flight_model',ROOT/'champions/v10.0/team.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    results=[]
    for name,direction,delay in [('upper-side',(0.,1.),0),('lower-side',(0.,-1.),0),
                                 ('oblique-side',(.6,.8),0),('end-wall',(.98,.2),12)]:
        helper=module.Guardiola2011();rows=[];forecast=None;motion=None;native_bounces=0
        kicked=False;postkick=0;start=None;previous=None;max_error=0.
        with SoccerEnv(config_path=str(ROOT/'configs/default.toml'),max_ticks=2400,per_decision_timeout_ms=20.) as env:
            assert env.engine_version=='0.1.0' and env.config_hash=='372990895c7eca2a'
            assert env.config()['ball']['wall_restitution']==.75
            assert env.config()['ball']['friction_per_tick']==.985
            assert not env.config()['ball']['aerial']
            assert env.set_formation(0,[(-47.,0.),(-38.,-22.),(-27.,-22.),(-17.,-22.),(-10.8,0.)])==0
            assert env.set_formation(1,[(-47.,0.),(-38.,22.),(-27.,22.),(-17.,22.),(-10.8,22.)])==0
            observations=env.reset(seed=1001,kickoff_team=0);helper._setup(env.field)
            for _ in range(240):
                obs=observations['team_a']
                if kicked and obs.ball.last_touch==4:
                    postkick+=1
                    if forecast is None and postkick>delay:
                        start=obs.tick
                        # Enable only velocity recording on the unchanged
                        # public-physics path; its positions are identical.
                        helper.FIRST_TOUCH=True
                        forecast=helper._pass_path((*obs.ball.position,*obs.ball.velocity))
                        motion=helper._last_pass_motion[1]
                    if forecast is not None:
                        i=obs.tick-start
                        if i>=len(forecast):break
                        actual=(*obs.ball.position,*obs.ball.velocity)
                        predicted=(*forecast[i][1:],*motion[i])
                        error=max(abs(x-y) for x,y in zip(actual,predicted))
                        max_error=max(max_error,error)
                        if previous is not None:
                            for axis in (0,1):
                                if previous[axis+2]*actual[axis+2]<0.:
                                    native_bounces+=1
                        rows.append({'tick':obs.tick,'native':actual,'predicted':predicted,'max_error':error})
                        previous=actual
                a=TeamController.idle(obs)
                if not kicked:
                    p=next(p for p in obs.my_players if p.id==4)
                    move=helper._move((p.id,*p.position,*p.velocity),(obs.ball.position[0]+.3,obs.ball.position[1]))
                    if obs.can_kick(4):
                        length=math.hypot(*direction)
                        unit=(direction[0]/length,direction[1]/length)
                        a.set(4,PlayerAction(movement=move,kick_direction=unit,kick_power=1.))
                        kicked=True
                    else:a.set(4,PlayerAction(movement=move))
                observations,_=env.step({'team_a':a,'team_b':TeamController.idle(observations['team_b'])})
            assert rows and len(rows)==81,(name,len(rows))
            assert native_bounces>0,(name,'no observed rebound')
            assert max_error<.002,(name,max_error)
            results.append({'name':name,'direction':direction,'forecast_start_tick':start,
              'native_bounces':native_bounces,'max_position_velocity_error':max_error,'frames':rows})
            print(name,'native rebound verified; max error',max_error)
    dest=ROOT/'tests/fixtures/physics-native-flights.json'
    assert not dest.exists()
    dest.write_text(json.dumps({'scope':'Legal native physics fixtures; no state/configuration injection or policy-timing claim.',
       'engine_version':'0.1.0','config_hash':'372990895c7eca2a','flights':results},indent=2)+'\n')


if __name__=='__main__':main()
